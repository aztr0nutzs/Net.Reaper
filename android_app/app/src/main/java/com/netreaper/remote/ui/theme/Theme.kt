package com.netreaper.remote.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFFc9d1ff),
    onPrimary = Color(0xFF050510),
    primaryContainer = Color(0xFF4b00ff),
    onPrimaryContainer = Color(0xFFc9d1ff),
    secondary = Color(0xFF00c6ff),
    onSecondary = Color(0xFF050510),
    secondaryContainer = Color(0xFF562dff),
    onSecondaryContainer = Color(0xFFc9d1ff),
    tertiary = Color(0xFF6c34ff),
    onTertiary = Color(0xFFc9d1ff),
    error = Color(0xFFff4444),
    onError = Color(0xFFffffff),
    errorContainer = Color(0xFFff4444),
    onErrorContainer = Color(0xFFffffff),
    background = Color(0xFF050510),
    onBackground = Color(0xFFc9d1ff),
    surface = Color(0xFF0e0b1f),
    onSurface = Color(0xFFc9d1ff),
    surfaceVariant = Color(0xFF1f1a3d),
    onSurfaceVariant = Color(0xFFc9d1ff),
    outline = Color(0xFF312162)
)

@Composable
fun NetReaperRemoteTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        typography = Typography,
        content = content
    )
}