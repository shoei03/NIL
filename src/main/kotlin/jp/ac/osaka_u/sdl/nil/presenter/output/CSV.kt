package jp.ac.osaka_u.sdl.nil.presenter.output

import jp.ac.osaka_u.sdl.nil.entity.CodeBlockInfo

/**
 * NIL's standard output format is "/path/to/file1,start_line1,end_line1,/path/to/file2,start_line2,end_line2",
 * as well as CCAligner.
 * Now includes method information if available.
 */
class CSV : Format() {
    override fun reformat(codeBlock1: CodeBlockInfo, codeBlock2: CodeBlockInfo): String =
        "${codeBlock1.toFullString()},${codeBlock2.toFullString()}"
}
