const WebsocketWrapper = class {
    constructor(url,receiveCallback) {
      this._opened = false
      this._websocket = new WebSocket(url);

      this._websocket.onopen = (event) => {
        this.log('websocket opened');
        this._opened = true
      }

      this._websocket.onclose = (event) => {
        this.log('websocket closed');
        this._opened = false
      }

      this._websocket.onmessage = (event) => {
        try{
          if(receiveCallback){
            var _data = JSON.parse(event.data)
            receiveCallback(_data)
          }
        }catch(e){
          this.log(e);
        }
        this.log('received: '+event.data);
      }
    }

    log(data){
        // console.log(data)
    }

    send(data){
        // TODO: Encryption - Public key from server
        if(this._opened){
          try{
            const _json = JSON.stringify(data);
            this._websocket.send(_json);
            this.log('sent: '+_json);
          }catch(e){
            this.log(e);
          }
        }   
    }
  }
