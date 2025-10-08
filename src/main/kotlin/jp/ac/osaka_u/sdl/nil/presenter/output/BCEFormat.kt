package jp.ac.osaka_u.sdl.nil.presenter.output

import jp.ac.osaka_u.sdl.nil.entity.CodeBlockInfo
import java.io.File

/**
 * BigCloneEval Format is as "dir1,file_name1,start_line1,end_line1,dir2,file_name2,start_line2,end_line2"
 */
class BCEFormat : Format() {
    override fun reformat(codeBlock1: CodeBlockInfo, codeBlock2: CodeBlockInfo): String =
        "${extractBCEFormat(codeBlock1)},${extractBCEFormat(codeBlock2)}"

    private fun extractBCEFormat(codeBlock: CodeBlockInfo): String {
        val (dirName, fileName) = codeBlock.fileName.split(File.separator)
            .let { it[it.size - 2] to it.last() }
        return "$dirName,$fileName,${codeBlock.startLine},${codeBlock.endLine}"
    }
}
