SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
RX_UUID      = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
TX_UUID      = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

sendCharacteristic = null;

function doit(){

    navigator.bluetooth.requestDevice(
        { filters: [{ services: [SERVICE_UUID] }]
        }).then(
            device => { console.log('Connecting to GATT Server...'); 
                        return device.gatt.connect(); 
                      }).then(
            server => { console.log(server)
                        console.log('Getting Services...');
                        return server.getPrimaryService(SERVICE_UUID);}).then(
            service => {    service.getCharacteristic(TX_UUID).then(
                                characteristic => characteristic.startNotifications()).then(
                                characteristic => characteristic.addEventListener(
                                                    'characteristicvaluechanged',
                                                    handleCharacteristicValueChanged)).catch(
                                                        error => console.log('Argh! ' + error));
                            service.getCharacteristic(RX_UUID).then(
                                characteristic => sendCharacteristic = characteristic).catch(
                                    error => console.log('Argh! ' + error));
                                }

        ).catch(error => console.log('Argh! ' + error));
}

function handleCharacteristicValueChanged(event) {
    const value = event.target.value;
    str_value = new TextDecoder("utf-8").decode(value)
    console.log('Received ' + str_value);
    v = parseInt(str_value);
    if(v & 2 ) {document.getElementById("left").style.backgroundColor = "Red"} else {document.getElementById("left").style.backgroundColor = "White"}
    if(v & 1 ) {document.getElementById("right").style.backgroundColor = "Red"} else {document.getElementById("right").style.backgroundColor = "White"}
    if(v & 4 ) {document.getElementById("top").style.backgroundColor = "Red"} else {document.getElementById("top").style.backgroundColor = "White"}
    if(v & 8 ) {document.getElementById("down").style.backgroundColor = "Red"} else {document.getElementById("down").style.backgroundColor = "White"}
    if(v & 16 ) {document.getElementById("button").style.backgroundColor = "Red"} else {document.getElementById("button").style.backgroundColor = "White"}

    if(sendCharacteristic) sendCharacteristic.writeValue(new TextEncoder("utf-8").encode('thanx for ' + str_value))
  }

// see also:
// https://developer.chrome.com/articles/bluetooth/
// https://loginov-rocks.github.io/Web-Bluetooth-Terminal/
// https://developer.mozilla.org/en-US/docs/Web/API/BluetoothDevice
// https://github.com/loginov-rocks/Web-Bluetooth-Terminal

