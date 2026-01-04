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
            onTextChanged: {
                suggestionModel.clear()
                const query = text.trim().toLowerCase()
                if (!query) {
                    return
                }
                for (let i = 0; i < tts.phrasesModel.count; i += 1) {
                    const item = tts.phrasesModel.get(i)
                    const phrase = item.display || ""
                    if (phrase.toLowerCase().indexOf(query) !== -1) {
                        suggestionModel.append({ display: phrase })
                    }
                }
            }
        }

        Popup {
            id: suggestionPopup
            x: inputText.x
            y: inputText.y + inputText.height + 4
            width: inputText.width
            modal: false
            focus: false
            closePolicy: Popup.CloseOnPressOutside
            visible: inputText.activeFocus && suggestionModel.count > 0

            ListView {
                id: suggestionList
                width: parent.width
                height: Math.min(contentHeight, 160)
                model: suggestionModel
                clip: true
                delegate: ItemDelegate {
                    width: ListView.view.width
                    text: model.display
                    onClicked: {
                        inputText.text = model.display
                        suggestionPopup.close()
                        inputText.forceActiveFocus()
                    }
                }
            }
        }

        ListModel {
            id: suggestionModel
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

            Button {
                text: "Save"
                onClicked: tts.save(inputText.text)
            }

            Button {
                text: "Озвучить"
                onClicked: tts.say(inputText.text)
            }
        }
    }
}
