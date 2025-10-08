package jp.ac.osaka_u.sdl.nil.presenter.output

import jp.ac.osaka_u.sdl.nil.NILMain
import jp.ac.osaka_u.sdl.nil.NILMain.Companion.CODE_BLOCK_FILE_NAME
import jp.ac.osaka_u.sdl.nil.entity.CodeBlockInfo
import java.io.File

abstract class Format {
    fun convert(outputFileName: String) =
        File(outputFileName).bufferedWriter().use { bw ->
            val codeBlocks: List<CodeBlockInfo> = File(CODE_BLOCK_FILE_NAME)
                .readLines()
                .map { CodeBlockInfo.parse(it) }
            File(NILMain.CLONE_PAIR_FILE_NAME).bufferedReader().use { br ->
                br.lines()
                    .map { line ->
                        val parts = line.split(",")
                        val id1 = parts[0].toInt()
                        val id2 = parts[1].toInt()
                        val nGramSimilarity = if (parts.size > 2 && parts[2].isNotEmpty()) parts[2] else null
                        val lcsSimilarity = if (parts.size > 3 && parts[3].isNotEmpty()) parts[3] else null
                        val codeBlock1 = codeBlocks[id1]
                        val codeBlock2 = codeBlocks[id2]
                        reformat(codeBlock1, codeBlock2, nGramSimilarity, lcsSimilarity)
                    }
                    .forEach { bw.appendLine(it) }
            }
        }

    protected abstract fun reformat(
        codeBlock1: CodeBlockInfo, 
        codeBlock2: CodeBlockInfo,
        nGramSimilarity: String?,
        lcsSimilarity: String?
    ): String
}
