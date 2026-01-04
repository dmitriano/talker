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
                if (activeFocus && text.trim().length > 0) {
                    suggestionPopup.open()
                } else {
                    suggestionPopup.close()
                }
            }
            onActiveFocusChanged: {
                if (!activeFocus) {
                    suggestionPopup.close()
                } else if (text.trim().length > 0) {
                    suggestionPopup.open()
                }
            }
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

    Popup {
        id: suggestionPopup
        parent: window.contentItem
        readonly property point inputBottom: inputText.mapToItem(window.contentItem, 0, inputText.height)
        x: inputBottom.x
        y: inputBottom.y
        width: inputText.width
        padding: 4
        modal: false
        focus: false
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle {
            color: "#1e1e1e"
            border.color: "#4c4c4c"
            radius: 6
        }

        ListView {
            id: suggestionsView
            width: parent.width
            height: Math.min(contentHeight, 160)
            clip: true
            model: tts.phrasesModel
            property string filterText: inputText.text.trim().toLowerCase()

            delegate: Item {
                required property string modelData
                readonly property bool matches: suggestionsView.filterText.length > 0
                    && modelData.toLowerCase().indexOf(suggestionsView.filterText) !== -1
                width: ListView.view.width
                height: matches ? textItem.implicitHeight + 10 : 0
                visible: matches

                Text {
                    id: textItem
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 8
                    color: "white"
                    text: modelData
                    elide: Text.ElideRight
                    width: parent.width - 16
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        inputText.text = modelData
                        suggestionPopup.close()
                        inputText.forceActiveFocus()
                    }
                }
            }

            onContentHeightChanged: {
                if (inputText.activeFocus && contentHeight > 0) {
                    suggestionPopup.open()
                } else {
                    suggestionPopup.close()
                }
            }
        }
    }
}
