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
    echo "  $0 /app/target_project -mil 10 -mit 100"
    echo "  $0 /app/target_project -l python -o results.csv"
    echo ""
    echo "よく使われるオプション:"
    echo "  -mil, --min-line NUM       最小行数 (デフォルト: 6)"
    echo "  -mit, --min-token NUM      最小トークン数 (デフォルト: 50)"
    echo "  -l, --language LANG        言語 (java, c, cpp, cs, python, kotlin)"
    echo "  -o, --output FILE          出力ファイル"
    echo "  -t, --threads NUM          スレッド数"
    echo "  -p, --partition-size NUM   パーティション数 (デフォルト: 10)"
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

# 引数があれば shift（デフォルト値使用時は shift しない）
if [ $# -gt 0 ]; then
    shift
fi

echo "🔍 NIL クローン検出を実行中..."
echo "📁 ソースディレクトリ: $SOURCE_DIR"

# JARファイルが存在するかチェック
if ! docker compose run --rm nil test -f ./build/libs/NIL-all.jar; then
    echo "❌ NIL-all.jarが見つかりません。先にビルドを実行してください："
    echo "   ./scripts/build.sh"
    exit 1
fi

# NILを実行
docker compose run --rm nil java -jar ./build/libs/NIL-all.jar -s "$SOURCE_DIR" -l "python" -o "./results/results.csv" "$@"

echo "✅ NIL クローン検出が完了しました"
echo "📊 結果ファイルを確認してください"