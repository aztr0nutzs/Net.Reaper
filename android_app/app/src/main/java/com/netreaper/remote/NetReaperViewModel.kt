package com.netreaper.remote

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
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
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
    private val _target = MutableStateFlow("")
    val target: StateFlow<String> = _target.asStateFlow()

    private val _networkInterface = MutableStateFlow("")
    val networkInterface: StateFlow<String> = _networkInterface.asStateFlow()

    private val _hostInput = MutableStateFlow("")
    val hostInput: StateFlow<String> = _hostInput.asStateFlow()

    private val _passwordInput = MutableStateFlow("")
    val passwordInput: StateFlow<String> = _passwordInput.asStateFlow()

    private val _log = MutableStateFlow<List<String>>(emptyList())
    val log: StateFlow<List<String>> = _log.asStateFlow()

    private val _connectionMessages = MutableStateFlow<List<String>>(emptyList())
    val connectionMessages: StateFlow<List<String>> = _connectionMessages.asStateFlow()

    private val _pairingFeedback = MutableStateFlow<List<String>>(emptyList())
    val pairingFeedback: StateFlow<List<String>> = _pairingFeedback.asStateFlow()

    private val _status = MutableStateFlow("STANDBY")
    val status: StateFlow<String> = _status.asStateFlow()

    private val _pulse = MutableStateFlow(0)
    val pulse: StateFlow<Int> = _pulse.asStateFlow()

    private val _latency = MutableStateFlow(10)
    val latency: StateFlow<Int> = _latency.asStateFlow()

    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    private val _pairingCode = MutableStateFlow("")
    val pairingCode: StateFlow<String> = _pairingCode.asStateFlow()

    private val _remotePaired = MutableStateFlow(false)
    val remotePaired: StateFlow<Boolean> = _remotePaired.asStateFlow()

    private val _guiPaired = MutableStateFlow(false)
    val guiPaired: StateFlow<Boolean> = _guiPaired.asStateFlow()

    private val _connectedDevices = MutableStateFlow<List<String>>(emptyList())
    val connectedDevices: StateFlow<List<String>> = _connectedDevices.asStateFlow()

    private val client = HttpClient(CIO) {
        install(WebSockets)
        install(ContentNegotiation) {
            json(Json { prettyPrint = true; isLenient = true })
        }
    }

    private var session: DefaultWebSocketSession? = null

    fun setTarget(target: String) {
        _target.value = target
    }

    fun setNetworkInterface(networkInterface: String) {
        _networkInterface.value = networkInterface
    }

    fun setHostInput(hostInput: String) {
        _hostInput.value = hostInput
    }

    fun setPasswordInput(passwordInput: String) {
        _passwordInput.value = passwordInput
    }

    fun connect(host: String, password: String) {
        viewModelScope.launch {
            _connectionState.value = ConnectionState.CONNECTING
            _status.value = "CONNECTING"
            try {
                val token = authenticate(host, password)
                if (token != null) {
                    client.webSocket(host = host, port = 8443, path = "/ws") {
                        session = this
                        send(Frame.Text("{\"token\":\"$token\"}"))
                        val authResponse = incoming.receive() as? Frame.Text
                        if (authResponse?.readText()?.contains("authenticated") == true) {
                            _status.value = "CONNECTED"
                            _connectionState.value = ConnectionState.CONNECTED
                            addConnectionMessage("Authenticated to $host")
                            listenForMessages()
                        } else {
                            addLog("Authentication failed")
                            addConnectionMessage("Authentication failed for $host")
                            _connectionState.value = ConnectionState.DISCONNECTED
                        }
                    }
                } else {
                    addLog("Authentication failed")
                    addConnectionMessage("Authentication failed for $host")
                    _connectionState.value = ConnectionState.DISCONNECTED
                }
            } catch (e: Exception) {
                addLog("Connection error: ${e.message}")
                addConnectionMessage("Connection error: ${e.message}")
                _connectionState.value = ConnectionState.DISCONNECTED
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
            addLog("Auth error: ${e.message}")
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
                _pairingCode.value = response.pairCode
                _remotePaired.value = true
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
                _pairingCode.value = response.pairCode
                _guiPaired.value = true
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
                        addLog(json["output"]!!.jsonPrimitive.content)
                    } else if (json.containsKey("error")) {
                        addLog("Error: ${json["error"]!!.jsonPrimitive.content}")
                    }
                } catch (e: Exception) {
                    addLog(text)
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
            _status.value = "DISCONNECTED"
            _connectionState.value = ConnectionState.DISCONNECTED
            addConnectionMessage("Disconnected manually")
        }
    }

    private fun onConnectionClosed() {
        _connectionState.value = ConnectionState.DISCONNECTED
        if (status.value == "CONNECTED") {
            _status.value = "DISCONNECTED"
            addConnectionMessage("Remote bridge closed")
        }
    }

    private fun addLog(message: String) {
        _log.value = _log.value + message
    }

    private fun addConnectionMessage(message: String) {
        _connectionMessages.value = _connectionMessages.value + "${System.currentTimeMillis()}: $message"
        if (connectionMessages.value.size > 20) {
            _connectionMessages.value = _connectionMessages.value.drop(1)
        }
    }

    private fun addPairingFeedback(message: String) {
        _pairingFeedback.value = _pairingFeedback.value + message
        if (pairingFeedback.value.size > 12) {
            _pairingFeedback.value = _pairingFeedback.value.drop(1)
        }
    }

    override fun onCleared() {
        super.onCleared()
        client.close()
    }
}
