import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 860
    height: 520
    title: "Говорилка"
    property int maxInputLength: 1000
    property color statusColor: "blue"
    property string selectedFavorite: ""

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

        RowLayout {
            Layout.fillWidth: true

            Item {
                Layout.fillWidth: true
            }

            Label {
                text: "Символов: " + inputText.text.length + " / " + window.maxInputLength
                    + " (осталось " + Math.max(window.maxInputLength - inputText.text.length, 0) + ")"
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

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: "Избранное"
                    Layout.alignment: Qt.AlignVCenter
                }

                Item {
                    Layout.fillWidth: true
                }

                Button {
                    text: "В избранное"
                    enabled: inputText.text.length > 0
                    onClicked: tts.addFavorite(inputText.text)
                }

                Button {
                    text: "Удалить из избранного"
                    enabled: window.selectedFavorite.length > 0
                    onClicked: {
                        tts.removeFavorite(window.selectedFavorite)
                        window.selectedFavorite = ""
                    }
                }
            }

            ListView {
                id: favoritesList
                Layout.fillWidth: true
                Layout.preferredHeight: 110
                clip: true
                model: tts.favoritesModel

                delegate: ItemDelegate {
                    width: favoritesList.width
                    text: model.display
                    highlighted: ListView.isCurrentItem
                    onClicked: {
                        favoritesList.currentIndex = index
                        window.selectedFavorite = model.display
                        inputText.text = model.display
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "Категория"
                Layout.alignment: Qt.AlignVCenter
            }

            ComboBox {
                id: categoryPicker
                Layout.fillWidth: true
                model: tts.categoriesModel
                textRole: "display"
                editable: false
                onActivated: tts.setCurrentCategory(currentText)
                Component.onCompleted: currentIndex = find(tts.currentCategory)
            }

            Button {
                text: "Добавить"
                onClicked: addCategoryDialog.open()
            }

            Button {
                text: "Удалить"
                enabled: categoryPicker.currentText.length > 0
                onClicked: tts.removeCategory(categoryPicker.currentText)
            }
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
                text: "Preparing..."
                visible: tts.preparing
                color: window.statusColor
                Layout.alignment: Qt.AlignVCenter
            }

            Label {
                text: "Playing..."
                visible: tts.playing
                color: window.statusColor
                Layout.alignment: Qt.AlignVCenter
            }

            Label {
                text: "Сохранение..."
                visible: tts.saving
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

            Button {
                text: "В файл"
                onClicked: tts.saveAudio(inputText.text)
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

        function onCurrentCategoryChanged() {
            categoryPicker.currentIndex = categoryPicker.find(tts.currentCategory)
        }

        function onCategoriesChanged() {
            categoryPicker.currentIndex = categoryPicker.find(tts.currentCategory)
        }
    }

    Dialog {
        id: addCategoryDialog
        title: "Новая категория"
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        closePolicy: Popup.CloseOnEscape

        ColumnLayout {
            anchors.fill: parent
            spacing: 8

            TextField {
                id: categoryNameField
                Layout.fillWidth: true
                placeholderText: "Введите название категории"
            }
        }

        onAccepted: {
            tts.addCategory(categoryNameField.text)
            categoryNameField.text = ""
        }

        onRejected: {
            categoryNameField.text = ""
        }
    }
}
