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
    val parameters: List<Parameter>? = null,
    val commitHash: String? = null,
    val tokenHash: String? = null,
    val tokenSequence: List<Int>? = null
) {
    companion object {
        /**
         * Parse a line from code_blocks file.
         * Supports multiple formats:
         * 
         * Old format: /path/to/file,10,25
         * Method format: /path/to/file,10,25,method_name,return_type,[param1:type1;param2:type2]
         * Extended format: /path/to/file,10,25,method_name,return_type,[params],commit_hash,token_hash
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
                // Extended format with commit hash and token hash
                parts.size >= 8 -> {
                    val fileName = parts[0]
                    val startLine = parts[1].toInt()
                    val endLine = parts[2].toInt()
                    val methodName = parts[3]
                    val returnType = parts[4]
                    
                    // Parse parameters from [param1:type1;param2:type2;...]
                    // Find the parameters section between brackets
                    val paramStart = line.indexOf('[')
                    val paramEnd = line.indexOf(']', paramStart)
                    val paramString = if (paramStart >= 0 && paramEnd > paramStart) {
                        line.substring(paramStart + 1, paramEnd)
                    } else {
                        ""
                    }
                    val parameters = parseParameters(paramString)
                    
                    // Parse token sequence from [token1;token2;...]
                    // Find the token sequence section (last bracketed section)
                    val tokenSeqStart = line.lastIndexOf('[')
                    val tokenSeqEnd = line.lastIndexOf(']')
                    val tokenSequence = if (tokenSeqStart > paramEnd && tokenSeqEnd > tokenSeqStart) {
                        val tokenSeqString = line.substring(tokenSeqStart + 1, tokenSeqEnd)
                        if (tokenSeqString.isNotEmpty()) {
                            tokenSeqString.split(";").mapNotNull { it.toIntOrNull() }
                        } else {
                            null
                        }
                    } else {
                        null
                    }
                    
                    // Get commit hash and token hash
                    // They are between the parameter bracket and token sequence bracket
                    val afterParams = if (paramEnd >= 0) line.substring(paramEnd + 1) else line
                    val beforeTokenSeq = if (tokenSeqStart > paramEnd) {
                        afterParams.substring(0, tokenSeqStart - paramEnd - 1)
                    } else {
                        afterParams
                    }
                    val hashParts = beforeTokenSeq.split(",").filter { it.isNotEmpty() }
                    val commitHash = hashParts.getOrNull(hashParts.size - 2)
                    val tokenHash = hashParts.getOrNull(hashParts.size - 1)
                    
                    CodeBlockInfo(
                        fileName = fileName,
                        startLine = startLine,
                        endLine = endLine,
                        methodName = methodName.takeIf { it.isNotEmpty() && it != "null" },
                        returnType = returnType.takeIf { it.isNotEmpty() && it != "null" && it != "None" },
                        parameters = parameters,
                        commitHash = commitHash?.takeIf { it.isNotEmpty() && it != "null" && it != "unknown" },
                        tokenHash = tokenHash?.takeIf { it.isNotEmpty() && it != "null" },
                        tokenSequence = tokenSequence
                    )
                }
                // Method format: fileName,startLine,endLine,methodName,returnType,[params]
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
            // Replace commas with semicolons in parameter names and types to avoid CSV parsing issues
            val paramStr = parameters?.joinToString(";") { 
                "${it.name.replace(",", ";")}:${it.type.replace(",", ";")}" 
            } ?: ""
            // Replace commas in return type as well
            val sanitizedReturnType = (returnType ?: "None").replace(",", ";")
            "$fileName,$startLine,$endLine,$methodName,$sanitizedReturnType,[$paramStr]"
        } else {
            toBasicString()
        }
    }
}
