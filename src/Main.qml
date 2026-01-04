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
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "Голос"
                Layout.alignment: Qt.AlignVCenter
            }

            ComboBox {
                id: speakerPicker
                Layout.fillWidth: true
                model: tts.speakersModel
                textRole: "display"
                editable: false
                onActivated: tts.speaker = currentText
                Component.onCompleted: currentIndex = find(tts.speaker)
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "Скорость"
                Layout.alignment: Qt.AlignVCenter
            }

            ComboBox {
                id: speedPicker
                Layout.fillWidth: true
                model: ListModel {
                    ListElement { text: "0.8x"; value: 0.8 }
                    ListElement { text: "1.0x"; value: 1.0 }
                    ListElement { text: "1.2x"; value: 1.2 }
                }
                textRole: "text"
                editable: false
                onActivated: tts.speed = model.get(currentIndex).value
                Component.onCompleted: currentIndex = find("1.0x")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "Playing..."
                visible: tts.playing
                Layout.alignment: Qt.AlignVCenter
            }

            Item {
                Layout.fillWidth: true
            }

            CheckBox {
                text: "Autosave"
                checked: tts.autosave
                onToggled: tts.autosave = checked
            }

            CheckBox {
                id: editModeToggle
                text: "Edit Mode"
                checked: false
            }
            
            Button {
                text: "Save"
                onClicked: tts.save(inputText.text)
            }

            Button {
                text: "Удалить"
                enabled: editModeToggle.checked && phrasePicker.currentText.length > 0
                onClicked: tts.removePhrase(phrasePicker.currentText)
            }

            Button {
                text: "Озвучить"
                onClicked: tts.say(inputText.text)
            }
        }
    }

    Connections {
        target: tts
        function onSpeakerChanged() {
            speakerPicker.currentIndex = speakerPicker.find(tts.speaker)
        }

        function onSpeedChanged() {
            var label = Number(tts.speed).toFixed(1) + "x"
            speedPicker.currentIndex = speedPicker.find(label)
        }
    }
}
