#!/bin/bash

# NIL クローン検出実行スクリプト
# よく使われるオプションでNILを実行するための便利スクリプト

set -e

# 使用方法を表示する関数
show_usage() {
    echo "使用方法: $0 [ソースディレクトリ] [オプション]"
    echo ""
    echo "引数なしで実行した場合、デフォルトディレクトリ (/app/Repos/pandas) を使用します。"
    echo ""
    echo "例:"
    echo "  $0                                      # デフォルト値で実行"
    echo "  $0 /app/target_project                  # 指定ディレクトリで実行"
    echo "  $0 /app/target_project -c abc123def     # 特定のコミットをチェックアウトして実行"
    echo "  $0 /app/target_project -mil 10 -mit 100"
    echo "  $0 /app/target_project -l python -o results.csv"
    echo ""
    echo "チェックアウトオプション:"
    echo "  -c, --commit HASH          指定されたコミットハッシュにチェックアウト"
    echo "  --no-restore               実行後に元のブランチ/コミットに戻らない"
    echo ""
    echo "よく使われるオプション:"
    echo "  -mil, --min-line NUM       最小行数 (デフォルト: 6)"
    echo "  -mit, --min-token NUM      最小トークン数 (デフォルト: 50)"
    echo "  -l, --language LANG        言語 (java, c, cpp, cs, python, kotlin)"
    echo "  -o, --output FILE          出力ファイル"
    echo "  -t, --threads NUM          スレッド数"
    echo "  -p, --partition-size NUM   パーティション数 (デフォルト: 10)"
    echo ""
    echo "注意: -c オプションを使用した場合、結果ファイル名には"
    echo "      コミットの日時とハッシュが自動的に付与されます。"
    echo ""
    echo "完全なオプション一覧は以下で確認できます:"
    echo "  ./scripts/run.sh --help"
}

# 引数チェック（デフォルト値で実行可能）
if [ $# -eq 0 ]; then
    echo "ℹ️  引数が指定されていません。デフォルト値で実行します。"
    echo "   使用方法を確認したい場合は: $0 --help"
    echo ""
fi

# --help オプションの処理
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
fi

SOURCE_DIR="${1:-/app/Repos/pandas}"

# 変数の初期化
COMMIT_HASH=""
RESTORE_ORIGINAL=true
ORIGINAL_BRANCH=""
ORIGINAL_COMMIT=""
CUSTOM_OUTPUT=""

# 引数があれば shift（デフォルト値使用時は shift しない）
if [ $# -gt 0 ]; then
    shift
fi

# 残りの引数を解析
NIL_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--commit)
            COMMIT_HASH="$2"
            shift 2
            ;;
        --no-restore)
            RESTORE_ORIGINAL=false
            shift
            ;;
        -o|--output)
            CUSTOM_OUTPUT="$2"
            NIL_ARGS+=("$1" "$2")
            shift 2
            ;;
        *)
            NIL_ARGS+=("$1")
            shift
            ;;
    esac
done

echo "🔍 NIL クローン検出を実行中..."
echo "📁 ソースディレクトリ: $SOURCE_DIR"

# JARファイルが存在するかチェック
if ! docker compose run --rm nil test -f ./build/libs/NIL-all.jar; then
    echo "❌ NIL-all.jarが見つかりません。先にビルドを実行してください："
    echo "   ./scripts/build.sh"
    exit 1
fi

# Gitチェックアウト処理
if [ -n "$COMMIT_HASH" ]; then
    echo "🔄 指定されたコミット ($COMMIT_HASH) をチェックアウト中..."
    
    # 現在のブランチ/コミットを記録
    ORIGINAL_BRANCH=$(docker compose run --rm nil git -C "$SOURCE_DIR" branch --show-current 2>/dev/null | tr -d '\r')
    if [ -z "$ORIGINAL_BRANCH" ]; then
        # detached HEADの場合
        ORIGINAL_COMMIT=$(docker compose run --rm nil git -C "$SOURCE_DIR" rev-parse HEAD | tr -d '\r')
    fi
    
    # 指定されたコミットにチェックアウト
    if ! docker compose run --rm nil git -C "$SOURCE_DIR" checkout "$COMMIT_HASH"; then
        echo "❌ コミット $COMMIT_HASH のチェックアウトに失敗しました"
        exit 1
    fi
    
    # チェックアウト後のコミット情報を取得
    CURRENT_COMMIT=$(docker compose run --rm nil git -C "$SOURCE_DIR" rev-parse HEAD | tr -d '\r')
    COMMIT_TIMESTAMP=$(docker compose run --rm nil git -C "$SOURCE_DIR" show -s --format=%ct HEAD | tr -d '\r')
    
    # タイムスタンプを readable な形式に変換
    FORMATTED_TIME=$(date -r "$COMMIT_TIMESTAMP" "+%Y%m%d_%H%M%S" 2>/dev/null || date -d "@$COMMIT_TIMESTAMP" "+%Y%m%d_%H%M%S" 2>/dev/null)
    SHORT_COMMIT=${CURRENT_COMMIT:0:8}
    
    echo "✅ チェックアウト完了: $SHORT_COMMIT ($(date -r "$COMMIT_TIMESTAMP" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -d "@$COMMIT_TIMESTAMP" "+%Y-%m-%d %H:%M:%S" 2>/dev/null))"
fi

# 出力ファイル名を決定
if [ -z "$CUSTOM_OUTPUT" ] && [ -n "$COMMIT_HASH" ]; then
    OUTPUT_FILE="./results/results_${FORMATTED_TIME}_${SHORT_COMMIT}.csv"
    echo "📝 結果ファイル: $OUTPUT_FILE"
else
    OUTPUT_FILE="${CUSTOM_OUTPUT:-./results/results.csv}"
fi

# NILを実行
if [ -z "$CUSTOM_OUTPUT" ] && [ -n "$COMMIT_HASH" ]; then
    # コミット指定時は自動生成されたファイル名を使用
    docker compose run --rm nil java -jar ./build/libs/NIL-all.jar -s "$SOURCE_DIR" -l "python" -o "$OUTPUT_FILE" "${NIL_ARGS[@]}"
else
    # 通常の実行（-o オプションが含まれている場合も含む）
    docker compose run --rm nil java -jar ./build/libs/NIL-all.jar -s "$SOURCE_DIR" -l "python" -o "$OUTPUT_FILE" "${NIL_ARGS[@]}"
fi

# 元のブランチ/コミットに戻す処理
if [ "$RESTORE_ORIGINAL" = true ] && [ -n "$COMMIT_HASH" ]; then
    echo "🔄 元のブランチ/コミットに戻しています..."
    
    if [ -n "$ORIGINAL_BRANCH" ]; then
        docker compose run --rm nil git -C "$SOURCE_DIR" checkout "$ORIGINAL_BRANCH"
        echo "✅ ブランチ '$ORIGINAL_BRANCH' に戻しました"
    elif [ -n "$ORIGINAL_COMMIT" ]; then
        docker compose run --rm nil git -C "$SOURCE_DIR" checkout "$ORIGINAL_COMMIT"
        echo "✅ コミット '${ORIGINAL_COMMIT:0:8}' に戻しました"
    fi
elif [ "$RESTORE_ORIGINAL" = false ] && [ -n "$COMMIT_HASH" ]; then
    echo "ℹ️  元のブランチ/コミットには戻していません (--no-restore オプションが指定されました)"
fi

echo "✅ NIL クローン検出が完了しました"
if [ -n "$COMMIT_HASH" ]; then
    echo "📊 結果ファイル: $OUTPUT_FILE"
    echo "🕐 コミット日時: $(date -r "$COMMIT_TIMESTAMP" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -d "@$COMMIT_TIMESTAMP" "+%Y-%m-%d %H:%M:%S" 2>/dev/null)"
    echo "🔗 コミットハッシュ: $CURRENT_COMMIT"
else
    echo "📊 結果ファイルを確認してください"
fi