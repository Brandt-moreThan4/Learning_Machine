// ======================================================
// EASY CONFIG — edit these values only
// ======================================================
const CONFIG = {
  OUTPUT_FOLDER: 'output',                // All files saved here
  FILE_FORMAT: 'html',                    // 'html' or 'txt'
  MAX_EMAILS_PER_SOURCE: 10,              // cap per source after dedupe & sort
  SEARCH_LOCATION: 'in:inbox category:primary', // Gmail search scope
  PREFIX_SOURCE_IN_FILENAME: true,        // add source name at start of filename
  SOURCES: [
    {
      name: 'Money Stuff',
      senders: ['noreply@news.bloomberg.com'],
      terms: ['Matt Levine', 'Money Stuff']  // matched in subject/body
    },
    {
      name: 'Morning Brew',
      // add/remove senders you actually see in your inbox
      senders: ['hello@morningbrew.com', 'morningbrew@e.morningbrew.com', 'daily@morningbrew.com'],
      terms: ['Morning Brew']              // keep broad, refine if needed
    }
  ]
};
// ======================================================


// ===== MAIN =====
function saveNewsletterEmails() {
  Logger.log('=== Starting Newsletter Email Archive ===');

  try {
    const found = findEmailsForSources(CONFIG.SOURCES);
    if (found.length === 0) {
      Logger.log('No matching emails found. Try debugEmailSearch().');
      return;
    }

    Logger.log(`Found ${found.length} email threads across sources`);

    const outputFolder = getOrCreateFolder(CONFIG.OUTPUT_FOLDER);

    const fileUrls = saveIndividualEmailFiles(found, outputFolder);
    const sheetUrl = saveSummarySpreadsheet(found, outputFolder);

    Logger.log(`\n=== ARCHIVE COMPLETE ===`);
    Logger.log(`Threads processed: ${found.length}`);
    Logger.log(`Files created: ${fileUrls.length}`);
    Logger.log(`Summary spreadsheet: ${sheetUrl}`);

  } catch (err) {
    Logger.log('Error in main: ' + err.toString());
    Logger.log(err.stack);
  }
}


// ===== SEARCH =====
/**
 * Returns array of { thread, sourceName }
 */
function findEmailsForSources(sources) {
  /** @type {{thread: GoogleAppsScript.Gmail.GmailThread, sourceName: string}[]} */
  let results = [];

  sources.forEach((src) => {
    const { name, senders, terms } = src;
    const seenThreadIds = new Set();
    let threadsAll = [];

    // Build a few robust queries per source
    const queries = buildQueries(senders, terms, CONFIG.SEARCH_LOCATION);

    queries.forEach((q, i) => {
      Logger.log(`[${name}] Query ${i + 1}: ${q}`);
      const threads = GmailApp.search(q, 0, CONFIG.MAX_EMAILS_PER_SOURCE * 3); // oversample; dedupe later
      threads.forEach(t => {
        const id = t.getId();
        if (!seenThreadIds.has(id)) {
          seenThreadIds.add(id);
          threadsAll.push(t);
        }
      });
    });

    // Sort newest-last-message first
    threadsAll.sort((a, b) => {
      const da = a.getMessages()[a.getMessages().length - 1].getDate();
      const db = b.getMessages()[b.getMessages().length - 1].getDate();
      return db - da;
    });

    // Cap per source
    threadsAll = threadsAll.slice(0, CONFIG.MAX_EMAILS_PER_SOURCE);

    // Tag with source
    threadsAll.forEach(t => results.push({ thread: t, sourceName: name }));
  });

  return results;
}

function buildQueries(senders, terms, location) {
  const senderClauses = senders.map(s => `from:${s}`);
  const termClauses = terms.map(t => `"${t}"`);

  const senderOr = senderClauses.length ? `(${senderClauses.join(' OR ')})` : '';
  const termsOr = termClauses.length ? `(${termClauses.join(' OR ')})` : '';

  const base = [senderOr, termsOr, location].filter(Boolean).join(' ');

  const qs = [base];

  // Variants to catch edge cases
  if (senderClauses.length) qs.push(`${senderOr} ${location}`);
  if (termClauses.length) qs.push(`${termsOr} ${location}`);

  // individual term + all senders
  termClauses.forEach(tc => qs.push(`${senderOr} ${tc} ${location}`));

  // individual sender + all terms
  senderClauses.forEach(sc => qs.push(`${sc} ${termsOr} ${location}`));

  // unique
  return Array.from(new Set(qs));
}


// ===== SAVE FILES =====
/**
 * found = [{thread, sourceName}]
 */
function saveIndividualEmailFiles(found, outputFolder) {
  const urls = [];

  found.forEach(({ thread, sourceName }) => {
    const msgs = thread.getMessages();
    const m = msgs[msgs.length - 1];

    const subject = m.getSubject() || '';
    const dateStr = Utilities.formatDate(m.getDate(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
    const safeSubject = subject.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_').substring(0, 60) || 'No_Subject';
    const messageId = m.getId();
    const ext = CONFIG.FILE_FORMAT === 'html' ? 'html' : 'txt';

    const prefix = CONFIG.PREFIX_SOURCE_IN_FILENAME ? `${sourceName.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_')}_` : '';
    const fileName = `${prefix}${dateStr}_${safeSubject}_${messageId}.${ext}`;

    let content, mimeType;
    if (CONFIG.FILE_FORMAT === 'html') {
      content = getRawHtmlContent(m);
      mimeType = 'text/html';
    } else {
      content = getRawTextContent(m);
      mimeType = 'text/plain';
    }

    const blob = Utilities.newBlob(content, mimeType, fileName);
    const file = upsertFileInFolder(outputFolder, fileName, blob);
    urls.push(file.getUrl());

    Logger.log(`Saved (upserted): ${fileName}`);
  });

  return urls;
}


// ===== SUMMARY =====
function saveSummarySpreadsheet(found, outputFolder) {
  const sheetName = 'Email_Archive_Summary';
  deleteFilesByNameInFolder(outputFolder, sheetName); // overwrite

  const ss = SpreadsheetApp.create(sheetName);
  const sheet = ss.getActiveSheet();
  DriveApp.getFileById(ss.getId()).moveTo(outputFolder);

  const headers = ['#', 'Source', 'Date', 'Subject', 'From', 'To', 'Thread ID', 'Message ID', 'Suggested File Name'];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  const headerRange = sheet.getRange(1, 1, 1, headers.length);
  headerRange.setFontWeight('bold').setBackground('#4285f4').setFontColor('white');

  const rows = found.map(({ thread, sourceName }, i) => {
    const msgs = thread.getMessages();
    const m = msgs[msgs.length - 1];

    const subject = m.getSubject() || '';
    const date = m.getDate();
    const dateStr = Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyy-MM-dd');
    const safeSubject = subject.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_').substring(0, 60) || 'No_Subject';
    const messageId = m.getId();
    const ext = CONFIG.FILE_FORMAT === 'html' ? 'html' : 'txt';
    const prefix = CONFIG.PREFIX_SOURCE_IN_FILENAME ? `${sourceName.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_')}_` : '';
    const fileName = `${prefix}${dateStr}_${safeSubject}_${messageId}.${ext}`;

    return [
      i + 1,
      sourceName,
      date,
      subject,
      m.getFrom(),
      m.getTo(),
      thread.getId(),
      messageId,
      fileName
    ];
  });

  if (rows.length) sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);

  sheet.autoResizeColumns(1, headers.length);
  sheet.setColumnWidth(4, 320); // Subject
  sheet.setColumnWidth(5, 220); // From
  sheet.setColumnWidth(6, 220); // To
  sheet.setColumnWidth(9, 320); // File Name

  Logger.log(`Summary spreadsheet saved: ${ss.getUrl()}`);
  return ss.getUrl();
}


// ===== CONTENT BUILDERS =====
function getRawHtmlContent(message) {
  const subject = message.getSubject() || '';
  const date = message.getDate();
  const from = message.getFrom() || '';
  const to = message.getTo() || '';
  const cc = message.getCc() || '';
  const bcc = message.getBcc() || '';
  const htmlBody = message.getBody(); // raw HTML

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${escapeHtml(subject)}</title>
</head>
<body>
<!-- EMAIL METADATA -->
<!-- Subject: ${escapeHtml(subject)} -->
<!-- From: ${escapeHtml(from)} -->
<!-- To: ${escapeHtml(to)} -->
<!-- CC: ${escapeHtml(cc)} -->
<!-- BCC: ${escapeHtml(bcc)} -->
<!-- Date: ${date.toISOString()} -->
<!-- Thread ID: ${message.getThread().getId()} -->
<!-- Message ID: ${message.getId()} -->

<!-- RAW EMAIL CONTENT BELOW -->
${htmlBody}
</body>
</html>`;
}

function getRawTextContent(message) {
  const subject = message.getSubject() || '';
  const date = message.getDate();
  const from = message.getFrom() || '';
  const to = message.getTo() || '';
  const cc = message.getCc() || '';
  const bcc = message.getBcc() || '';
  const plainBody = message.getPlainBody();

  return `EMAIL METADATA
==============
Subject: ${subject}
From: ${from}
To: ${to}
CC: ${cc}
BCC: ${bcc}
Date: ${date.toISOString()}
Thread ID: ${message.getThread().getId()}
Message ID: ${message.getId()}

RAW EMAIL CONTENT
==================
${plainBody}`;
}


// ===== DRIVE HELPERS =====
function getOrCreateFolder(folderName) {
  const it = DriveApp.getFoldersByName(folderName);
  return it.hasNext() ? it.next() : DriveApp.createFolder(folderName);
}

function upsertFileInFolder(folder, fileName, blob) {
  deleteFilesByNameInFolder(folder, fileName);
  blob.setName(fileName);
  return folder.createFile(blob);
}

function deleteFilesByNameInFolder(folder, fileName) {
  const folderId = folder.getId();
  const safe = fileName.replace(/'/g, "\\'");
  const q = `title = '${safe}' and '${folderId}' in parents and trashed = false`;
  const it = DriveApp.searchFiles(q);
  while (it.hasNext()) it.next().setTrashed(true);
}

function escapeHtml(unsafe) {
  if (!unsafe) return '';
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}


// ===== DEBUG =====
function debugEmailSearch() {
  Logger.log('=== DEBUG: Sources & sample results ===');
  CONFIG.SOURCES.forEach((src) => {
    const queries = buildQueries(src.senders, src.terms, CONFIG.SEARCH_LOCATION).slice(0, 3);
    queries.forEach((q, i) => {
      Logger.log(`[${src.name}] Q${i + 1}: ${q}`);
      try {
        const threads = GmailApp.search(q, 0, 3);
        Logger.log(`  Found ${threads.length} threads`);
        threads.forEach((t, idx) => {
          const m = t.getMessages().pop();
          Logger.log(`    ${idx + 1}. ${m.getSubject()} | ${m.getFrom()} | ${m.getDate().toLocaleDateString()}`);
        });
      } catch (e) {
        Logger.log(`  Error: ${e}`);
      }
    });
  });
}
