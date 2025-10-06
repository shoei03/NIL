package jp.ac.osaka_u.sdl.nil.entity

/**
 * CodeBlockInfo represents parsed information from code_blocks file.
 * This class is used for output formatting.
 */
data class CodeBlockInfo(
    val fileName: String,
    val startLine: Int,
    val endLine: Int,
    val methodName: String? = null,
    val returnType: String? = null,
    val parameters: List<Parameter>? = null
) {
    companion object {
        /**
         * Parse a line from code_blocks file.
         * Supports both old format and new format with method information.
         * 
         * Old format: /path/to/file,10,25
         * New format: /path/to/file,10,25,method_name,return_type,[param1:type1;param2:type2]
         */
        fun parse(line: String): CodeBlockInfo {
            val parts = line.split(",")
            
            return when {
                // Old format: fileName,startLine,endLine
                parts.size == 3 -> {
                    CodeBlockInfo(
                        fileName = parts[0],
                        startLine = parts[1].toInt(),
                        endLine = parts[2].toInt()
                    )
                }
                // New format: fileName,startLine,endLine,methodName,returnType,[params]
                parts.size >= 6 -> {
                    val fileName = parts[0]
                    val startLine = parts[1].toInt()
                    val endLine = parts[2].toInt()
                    val methodName = parts[3]
                    val returnType = parts[4]
                    
                    // Parse parameters from [param1:type1;param2:type2;...]
                    val paramString = parts.drop(5).joinToString(",") // Re-join in case params contain commas
                    val parameters = parseParameters(paramString)
                    
                    CodeBlockInfo(
                        fileName = fileName,
                        startLine = startLine,
                        endLine = endLine,
                        methodName = methodName.takeIf { it.isNotEmpty() && it != "null" },
                        returnType = returnType.takeIf { it.isNotEmpty() && it != "null" && it != "None" },
                        parameters = parameters
                    )
                }
                else -> {
                    throw IllegalArgumentException("Invalid code block format: $line")
                }
            }
        }
        
        private fun parseParameters(paramString: String): List<Parameter>? {
            if (paramString.isEmpty() || paramString == "[]") {
                return null
            }
            
            // Remove surrounding brackets
            val cleaned = paramString.trim().removeSurrounding("[", "]")
            if (cleaned.isEmpty()) {
                return null
            }
            
            // Split by semicolon to get individual parameters
            return cleaned.split(";").mapNotNull { param ->
                val parts = param.split(":")
                if (parts.size == 2) {
                    Parameter(parts[0].trim(), parts[1].trim())
                } else {
                    null
                }
            }.takeIf { it.isNotEmpty() }
        }
    }
    
    /**
     * Convert to basic string format (fileName,startLine,endLine)
     * for backward compatibility.
     */
    fun toBasicString(): String = "$fileName,$startLine,$endLine"
    
    /**
     * Convert to full string format including method information.
     */
    fun toFullString(): String {
        return if (methodName != null) {
            val paramStr = parameters?.joinToString(";") { "${it.name}:${it.type}" } ?: ""
            "$fileName,$startLine,$endLine,$methodName,${returnType ?: "None"},[$paramStr]"
        } else {
            toBasicString()
        }
    }
}
