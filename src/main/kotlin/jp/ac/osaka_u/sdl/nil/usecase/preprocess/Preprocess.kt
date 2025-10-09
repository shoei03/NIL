package jp.ac.osaka_u.sdl.nil.usecase.preprocess

import io.reactivex.rxjava3.core.Flowable
import io.reactivex.rxjava3.schedulers.Schedulers
import jp.ac.osaka_u.sdl.nil.NILMain.Companion.CODE_BLOCK_DIR
import jp.ac.osaka_u.sdl.nil.NILMain.Companion.CODE_BLOCK_FILE_NAME
import jp.ac.osaka_u.sdl.nil.entity.CodeBlock
import jp.ac.osaka_u.sdl.nil.entity.TokenSequence
import jp.ac.osaka_u.sdl.nil.util.parallelIfSpecified
import java.io.File

/**
 * This is an abstract class for Preprocessing phase.
 * If you want to extend NIL to multiple languages,
 * all you have to do is extend this class
 * and write methods to collect the source files and code blocks of the language.
 */
abstract class Preprocess(private val threads: Int, private val commitHash: String? = null) {

    fun collectTokenSequences(src: File): List<TokenSequence> {
        // Create code_blocks directory if it doesn't exist
        val codeBlockDir = File(CODE_BLOCK_DIR)
        if (!codeBlockDir.exists()) {
            codeBlockDir.mkdirs()
        }
        
        val codeBlockFileName = if (commitHash != null) {
            "${CODE_BLOCK_DIR}/${CODE_BLOCK_FILE_NAME}_${commitHash.take(8)}"
        } else {
            "${CODE_BLOCK_DIR}/${CODE_BLOCK_FILE_NAME}"
        }
        
        val codeBlockFile = File(codeBlockFileName)
        
        return codeBlockFile.bufferedWriter().use { bw ->
            collectSourceFiles(src)
                .parallelIfSpecified(threads)
                .runOn(Schedulers.io())
                .flatMap { collectBlocks(it) }
                .sequential()
                .map { codeBlock -> 
                    // Add commit hash to code block
                    val blockWithCommit = if (commitHash != null && codeBlock.commitHash == null) {
                        codeBlock.copy(commitHash = commitHash)
                    } else {
                        codeBlock
                    }
                    bw.appendLine(blockWithCommit.toString())
                    blockWithCommit
                }
                .map { it.tokenSequence }
                .toList()
                .blockingGet()
        }
    }

    protected abstract fun collectSourceFiles(dir: File): Flowable<File>
    protected abstract fun collectBlocks(srcFile: File): Flowable<CodeBlock>
}
