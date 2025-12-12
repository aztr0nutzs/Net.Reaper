package com.netreaper.remote

import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.plugins.websocket.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.websocket.*
import kotlinx.coroutines.launch
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

enum class ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED
}

@Serializable
data class PairRequest(val deviceId: String, val role: String)

@Serializable
data class PairResponse(val pairCode: String, val status: String)

@Serializable
data class AuthRequest(val password: String)

@Serializable
data class AuthResponse(val token: String)

class NetReaperViewModel : ViewModel() {
    val target = mutableStateOf("")
    val interface = mutableStateOf("")
    val hostInput = mutableStateOf("")
    val passwordInput = mutableStateOf("")
    val log = mutableStateListOf<String>()
    val connectionMessages = mutableStateListOf<String>()
    val pairingFeedback = mutableStateListOf<String>()
    val status = mutableStateOf("STANDBY")
    val pulse = mutableStateOf(0)
    val latency = mutableStateOf(10)
    val connectionState = mutableStateOf(ConnectionState.DISCONNECTED)
    val pairingCode = mutableStateOf("")
    val remotePaired = mutableStateOf(false)
    val guiPaired = mutableStateOf(false)
    val connectedDevices = mutableStateListOf<String>()

    private val client = HttpClient(CIO) {
        install(WebSockets)
        install(ContentNegotiation) {
            json(Json { prettyPrint = true; isLenient = true })
        }
    }

    private var session: DefaultWebSocketSession? = null

    fun connect(host: String, password: String) {
        viewModelScope.launch {
            connectionState.value = ConnectionState.CONNECTING
            status.value = "CONNECTING"
            try {
                val token = authenticate(host, password)
                if (token != null) {
                    client.webSocket(host = host, port = 8443, path = "/ws") {
                        session = this
                        send(Frame.Text("{\"token\":\"$token\"}"))
                        val authResponse = incoming.receive() as? Frame.Text
                        if (authResponse?.readText()?.contains("authenticated") == true) {
                            status.value = "CONNECTED"
                            connectionState.value = ConnectionState.CONNECTED
                            addConnectionMessage("Authenticated to $host")
                            listenForMessages()
                        } else {
                            log.add("Authentication failed")
                            addConnectionMessage("Authentication failed for $host")
                            connectionState.value = ConnectionState.DISCONNECTED
                        }
                    }
                } else {
                    log.add("Authentication failed")
                    addConnectionMessage("Authentication failed for $host")
                    connectionState.value = ConnectionState.DISCONNECTED
                }
            } catch (e: Exception) {
                log.add("Connection error: ${e.message}")
                addConnectionMessage("Connection error: ${e.message}")
                connectionState.value = ConnectionState.DISCONNECTED
            }
        }
    }

    private suspend fun authenticate(host: String, password: String): String? {
        return try {
            val response: AuthResponse = client.post("https://$host:8443/auth") {
                contentType(ContentType.Application.Json)
                setBody(AuthRequest(password))
            }.body()
            response.token
        } catch (e: Exception) {
            log.add("Auth error: ${e.message}")
            null
        }
    }

    fun pairDevice(deviceId: String = "Android Remote") {
        viewModelScope.launch {
            val host = hostInput.value
            val password = passwordInput.value
            if (host.isBlank() || password.isBlank()) {
                addPairingFeedback("Host and password required for pairing")
                return@launch
            }
            val response = sendPairRequest(host, deviceId, "remote")
            if (response != null) {
                pairingCode.value = response.pairCode
                remotePaired.value = true
                addPairingFeedback("Remote paired: ${response.pairCode}")
            } else {
                addPairingFeedback("Remote pairing failed")
            }
        }
    }

    fun pairGui(deviceId: String = "NetReaper GUI") {
        viewModelScope.launch {
            val host = hostInput.value
            val password = passwordInput.value
            if (host.isBlank() || password.isBlank()) {
                addPairingFeedback("Host and password required for pairing")
                return@launch
            }
            val response = sendPairRequest(host, deviceId, "gui")
            if (response != null) {
                pairingCode.value = response.pairCode
                guiPaired.value = true
                addPairingFeedback("GUI paired: ${response.pairCode}")
            } else {
                addPairingFeedback("GUI pairing failed")
            }
        }
    }

    private suspend fun sendPairRequest(host: String, deviceId: String, role: String): PairResponse? {
        return try {
            client.post("https://$host:8443/pair") {
                contentType(ContentType.Application.Json)
                setBody(PairRequest(deviceId, role))
            }.body()
        } catch (e: Exception) {
            addPairingFeedback("Pair request error: ${e.message}")
            null
        }
    }

    private suspend fun DefaultWebSocketSession.listenForMessages() {
        for (frame in incoming) {
            if (frame is Frame.Text) {
                val text = frame.readText()
                try {
                    val json = Json.parseToJsonElement(text).jsonObject
                    if (json.containsKey("output")) {
                        log.add(json["output"]!!.jsonPrimitive.content)
                    } else if (json.containsKey("error")) {
                        log.add("Error: ${json["error"]!!.jsonPrimitive.content}")
                    }
                } catch (e: Exception) {
                    log.add(text)
                }
            }
        }
        onConnectionClosed()
    }

    fun executeCommand(command: String) {
        viewModelScope.launch {
            session?.send(Frame.Text("{\"command\":\"$command\"}"))
        }
    }

    fun disconnect() {
        viewModelScope.launch {
            session?.close()
            session = null
            status.value = "DISCONNECTED"
            connectionState.value = ConnectionState.DISCONNECTED
            addConnectionMessage("Disconnected manually")
        }
    }

    private fun onConnectionClosed() {
        connectionState.value = ConnectionState.DISCONNECTED
        if (status.value == "CONNECTED") {
            status.value = "DISCONNECTED"
            addConnectionMessage("Remote bridge closed")
        }
    }

    private fun addConnectionMessage(message: String) {
        connectionMessages.add("${System.currentTimeMillis()}: $message")
        if (connectionMessages.size > 20) {
            connectionMessages.removeFirst()
        }
    }

    private fun addPairingFeedback(message: String) {
        pairingFeedback.add(message)
        if (pairingFeedback.size > 12) {
            pairingFeedback.removeFirst()
        }
    }

    override fun onCleared() {
        super.onCleared()
        client.close()
    }
}
