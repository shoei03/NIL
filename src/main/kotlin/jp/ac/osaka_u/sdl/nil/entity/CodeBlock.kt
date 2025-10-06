package jp.ac.osaka_u.sdl.nil.entity

/**
 * Parameter represents a function parameter with its name and type.
 */
data class Parameter(
    val name: String,
    val type: String
)

/**
 * Code block is a single function.
 */
data class CodeBlock(
    val fileName: String,
    val startLine: Int,
    val endLine: Int,
    val tokenSequence: TokenSequence,
    val methodName: String? = null,
    val returnType: String? = null,
    val parameters: List<Parameter>? = null,
) {
    override fun toString(): String {
        return if (methodName != null) {
            val paramStr = parameters?.joinToString(";") { "${it.name}:${it.type}" } ?: ""
            "${fileName},${startLine},${endLine},${methodName},${returnType ?: "None"},[${paramStr}]"
        } else {
            "${fileName},${startLine},${endLine}"
        }
    }
}
