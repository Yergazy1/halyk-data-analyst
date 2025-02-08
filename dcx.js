function groupByEpic() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var range = sheet.getDataRange();
  var values = range.getValues();

  if (values.length <= 1) return; // Если только заголовки — выходим

  // Удаляем все предыдущие группировки
  removeAllGroups(sheet);

  try {
    sheet.expandAllRowGroups(); // Разворачиваем группы, если они есть
  } catch (e) {
    Logger.log("Нет групп для разворачивания: " + e);
  }

  sheet.unhideRow(sheet.getRange("A:A")); // Делаем все строки видимыми

  // Сортируем по столбцу A (эпик), пропуская заголовок
  var headers = values.shift();
  values.sort((a, b) => (a[0] || "").localeCompare(b[0] || ""));
  values.unshift(headers);

  // Обновляем таблицу
  sheet.getRange(1, 1, values.length, values[0].length).setValues(values);

  var lastEpic = "";
  var startRow = null;

  for (var i = 1; i < values.length; i++) {
    // Начинаем с 1, пропуская заголовок
    var epic = values[i][0]; // Теперь эпик находится в первом столбце

    if (epic !== lastEpic) {
      if (startRow !== null && i - startRow >= 1) {
        sheet.getRange(startRow, 1, i - startRow).shiftRowGroupDepth(1);
      }
      lastEpic = epic;
      startRow = i + 1;
    }
  }

  if (startRow !== null && values.length - startRow >= 1) {
    sheet.getRange(startRow, 1, values.length - startRow).shiftRowGroupDepth(1);
  }
}

// Функция для удаления всех группировок строк
function removeAllGroups(sheet) {
  var numRows = sheet.getLastRow();
  if (numRows > 1) {
    try {
      sheet.expandAllRowGroups();
      for (var i = 2; i <= numRows; i++) {
        sheet.getRange(i, 1).shiftRowGroupDepth(-1); // Убираем вложенность
      }
    } catch (e) {
      Logger.log("Ошибка при удалении группировок: " + e);
    }
  }
}
function doGet() {
  groupByEpic(); // Вызываем сортировку
  return ContentService.createTextOutput("Sorting completed");
}
