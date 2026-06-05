// ============================================================
// PASTE THIS IN: Google Sheet → Extensions → Apps Script
// Then: Deploy → New deployment → Web app
//   - Execute as: Me
//   - Who has access: Anyone
// Copy the deployment URL and paste it in index.html (line marked PASTE_URL_HERE)
// ============================================================

function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var data = JSON.parse(e.postData.contents);

  // Pick sheet tab by experiment: "Exp A" or "Exp B"
  var expName = data.experiment || 'A';
  var tabName = 'Exp ' + expName;
  var sheet = ss.getSheetByName(tabName);
  if (!sheet) {
    sheet = ss.insertSheet(tabName);
  }

  // Add header row if sheet is empty
  if (sheet.getLastRow() === 0) {
    sheet.appendRow([
      'timestamp', 'participant_id', 'experiment', 'age', 'gender',
      'education', 'native_speaker', 'region',
      'item_id', 'phenomenon', 'condition', 'rating', 'rt_ms', 'item_order'
    ]);
  }

  var rows = data.rows;
  for (var i = 0; i < rows.length; i++) {
    var r = rows[i];
    sheet.appendRow([
      r.timestamp, r.participant_id, r.experiment, r.age, r.gender,
      r.education, r.native_speaker, r.region,
      r.item_id, r.phenomenon, r.condition, r.rating, r.rt_ms, r.item_order
    ]);
  }

  return ContentService
    .createTextOutput(JSON.stringify({status: 'ok', count: rows.length}))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({status: 'ok', message: 'Use POST to submit data'}))
    .setMimeType(ContentService.MimeType.JSON);
}
