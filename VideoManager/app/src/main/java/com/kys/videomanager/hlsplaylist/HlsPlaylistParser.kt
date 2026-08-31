package com.kys.videomanager.hlsplaylist

import java.net.URI

data class HlsPlaylistParseResult(
    val isMaster: Boolean,
    val variantUrl: String?,
    val segmentUrls: List<String>,
    val isEncrypted: Boolean
)

object HlsPlaylistParser {
    private val bandwidthPattern = Regex("""BANDWIDTH=(\d+)""", RegexOption.IGNORE_CASE)
    private val uriAttributePattern = Regex("""URI="([^"]+)"""", RegexOption.IGNORE_CASE)

    fun parse(baseUrl: String, playlistText: String): HlsPlaylistParseResult {
        val variants = mutableListOf<Pair<Int, String>>()
        val segments = mutableListOf<String>()
        var pendingVariantBandwidth: Int? = null
        var encrypted = false

        playlistText.lineSequence()
            .map { it.trim() }
            .filter { it.isNotBlank() }
            .forEach { line ->
                when {
                    line.startsWith("#EXT-X-KEY", ignoreCase = true) &&
                        !line.contains("METHOD=NONE", ignoreCase = true) -> {
                        encrypted = true
                    }
                    line.startsWith("#EXT-X-MAP", ignoreCase = true) -> {
                        uriAttributePattern.find(line)?.groupValues?.getOrNull(1)?.let { uri ->
                            segments += resolveUrl(baseUrl, uri)
                        }
                    }
                    line.startsWith("#EXT-X-STREAM-INF", ignoreCase = true) -> {
                        pendingVariantBandwidth = bandwidthPattern.find(line)
                            ?.groupValues
                            ?.getOrNull(1)
                            ?.toIntOrNull() ?: 0
                    }
                    line.startsWith("#") -> Unit
                    pendingVariantBandwidth != null -> {
                        variants += pendingVariantBandwidth!! to resolveUrl(baseUrl, line)
                        pendingVariantBandwidth = null
                    }
                    else -> {
                        segments += resolveUrl(baseUrl, line)
                    }
                }
            }

        val selectedVariant = variants.maxByOrNull { it.first }?.second
        return HlsPlaylistParseResult(
            isMaster = variants.isNotEmpty(),
            variantUrl = selectedVariant,
            segmentUrls = if (variants.isEmpty()) segments else emptyList(),
            isEncrypted = encrypted
        )
    }

    private fun resolveUrl(baseUrl: String, value: String): String {
        return URI(baseUrl).resolve(value).toString()
    }
}
