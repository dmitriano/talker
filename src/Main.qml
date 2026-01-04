import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 640
    height: 360
    title: "Silero TTS"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            text: "Введите текст для озвучки"
            font.pixelSize: 18
        }

        TextArea {
            id: inputText
            Layout.fillWidth: true
            Layout.fillHeight: true
            placeholderText: "Напишите текст и нажмите \"Озвучить\""
            wrapMode: TextArea.Wrap
        }

        ComboBox {
            id: phrasePicker
            Layout.fillWidth: true
            model: tts.phrasesModel
            textRole: "display"
            editable: false
            onActivated: inputText.text = currentText
        }

        Button {
            text: "Озвучить"
            Layout.alignment: Qt.AlignRight
            onClicked: tts.say(inputText.text)
        }
    }
}
