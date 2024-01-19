# TailandBackend

## Подключение к комнате

javascript
const socket = new WebSocket('ws://78.40.219.212:8020/ws/chat/?token=');

socket.onopen = () => {
  // При успешном подключении
  socket.send(JSON.stringify({
    action: 'join_room',
    pk: 1  // Идентификатор комнаты, к которой пользователь хочет присоединиться
  }));
};

socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // Обработка полученного сообщения
};

socket.onclose = () => {
  // При закрытии соединения
};


## Отправка сообщения в комнату

javascript
socket.send(JSON.stringify({
  action: 'create_message',
  message: 'Привет, как дела?'  // Текст сообщения
}));


## Удаление сообщения

javascript
socket.send(JSON.stringify({
  action: 'delete_message',
  pk: 1  // Идентификатор удаляемого сообщения
}));


## Покинуть комнату

javascript
socket.send(JSON.stringify({
  action: 'leave_room',
  pk: 1  // Идентификатор комнаты, из которой пользователь хочет выйти
}));


## Подписаться на обновления сообщений в комнате

javascript
socket.send(JSON.stringify({
  action: 'subscribe_to_messages_in_room',
  pk: 1  // Идентификатор комнаты, на которую пользователь хочет подписаться
}));


## Создать сообщение с файлом

javascript
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

const formData = new FormData();
formData.append('file', file);
