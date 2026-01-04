import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 640
    height: 360
    title: "Silero TTS"

    Shortcut {
        sequences: ["Ctrl+Return", "Ctrl+Enter"]
        onActivated: tts.say(inputText.text)
    }
    
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

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8

            CheckBox {
                text: "Autosave"
                checked: tts.autosave
                onToggled: tts.autosave = checked
            }

            Button {
                text: "Save"
                onClicked: tts.save(inputText.text)
            }

            Button {
                text: "Удалить"
                enabled: phrasePicker.currentText.length > 0
                onClicked: tts.removePhrase(phrasePicker.currentText)
            }

            Button {
                text: "Озвучить"
                onClicked: tts.say(inputText.text)
            }
        }
    }
}
