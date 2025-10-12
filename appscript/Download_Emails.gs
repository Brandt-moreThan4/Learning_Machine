// ===== CONFIGURATION - Edit these parameters as needed =====
const CONFIG = {
  // Email search parameters
  MAX_EMAILS: 10,
  SENDER_EMAIL: 'noreply@news.bloomberg.com',
  SEARCH_TERMS: ['Matt Levine', 'Money Stuff'],

  // File output settings
  OUTPUT_FOLDER: 'output',
  FILE_FORMAT: 'html', // 'html' or 'txt'
  SAVE_INDIVIDUAL_FILES: true, // Save each email as separate file

  // Gmail search settings
  SEARCH_LOCATION: 'in:inbox category:primary' // Only search primary inbox
};

// ===== MAIN FUNCTION - Run this regularly =====
function saveMattLevineEmails() {
  Logger.log('=== Starting Matt Levine Email Archive Process ===');

  try {
    // Get emails
    const threads = findMattLevineEmails();

    if (threads.length === 0) {
      Logger.log('No Matt Levine emails found. Try running debugEmailSearch() to troubleshoot.');
      return;
    }

    Logger.log(`Found ${threads.length} Matt Levine email threads`);

    // Create (or reuse) output subfolder
    const outputFolder = getOrCreateFolder(CONFIG.OUTPUT_FOLDER);

    // Save each email as individual file (overwrite-by-name)
    const fileUrls = saveIndividualEmailFiles(threads, outputFolder);

    // Save summary spreadsheet (overwrite-by-name)
    const sheetUrl = saveSummarySpreadsheet(threads, outputFolder);

    // Log results
    Logger.log(`\n=== ARCHIVE COMPLETE ===`);
    Logger.log(`Emails processed: ${threads.length}`);
    Logger.log(`Files created: ${fileUrls.length}`);
    Logger.log(`Summary spreadsheet: ${sheetUrl}`);

  } catch (error) {
    Logger.log('Error in main function: ' + error.toString());
    Logger.log('Stack trace: ' + error.stack);
  }
}

// ===== CORE FUNCTIONS =====
function findMattLevineEmails() {
  const searchQueries = [
    `from:${CONFIG.SENDER_EMAIL} "${CONFIG.SEARCH_TERMS[0]}" ${CONFIG.SEARCH_LOCATION}`,
    `from:${CONFIG.SENDER_EMAIL} "${CONFIG.SEARCH_TERMS[1]}" ${CONFIG.SEARCH_LOCATION}`,
    `from:${CONFIG.SENDER_EMAIL} (${CONFIG.SEARCH_TERMS.join(' OR ')}) ${CONFIG.SEARCH_LOCATION}`
  ];

  let allThreads = [];
  let seenThreadIds = new Set();

  // Collect threads from all search queries, avoiding duplicates
  searchQueries.forEach((query, index) => {
    Logger.log(`Searching with query ${index + 1}: ${query}`);
    const threads = GmailApp.search(query, 0, CONFIG.MAX_EMAILS);

    threads.forEach(thread => {
      const threadId = thread.getId();
      if (!seenThreadIds.has(threadId)) {
        allThreads.push(thread);
        seenThreadIds.add(threadId);
      }
    });
  });

  // Sort threads by date (newest first)
  allThreads.sort((a, b) => {
    const dateA = a.getMessages()[a.getMessages().length - 1].getDate();
    const dateB = b.getMessages()[b.getMessages().length - 1].getDate();
    return dateB - dateA;
  });

  // Limit to MAX_EMAILS after deduplication and sorting
  return allThreads.slice(0, CONFIG.MAX_EMAILS);
}

function saveIndividualEmailFiles(threads, outputFolder) {
  const fileUrls = [];

  threads.forEach((thread) => {
    const messages = thread.getMessages();
    const latestMessage = messages[messages.length - 1];

    // Deterministic, collision-free filename using Message ID
    // (So we overwrite the exact same email file on re-runs.)
    const subject = latestMessage.getSubject();
    const date = Utilities.formatDate(latestMessage.getDate(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
    const safeSubject = subject ? subject.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_').substring(0, 50) : 'No_Subject';
    const messageId = latestMessage.getId(); // stable, unique per message
    const ext = CONFIG.FILE_FORMAT === 'html' ? 'html' : 'txt';
    const fileName = `${date}_${safeSubject}_${messageId}.${ext}`;

    // Get raw content with minimal processing
    let content;
    let mimeType;
    if (CONFIG.FILE_FORMAT === 'html') {
      content = getRawHtmlContent(latestMessage);
      mimeType = 'text/html';
    } else {
      content = getRawTextContent(latestMessage);
      mimeType = 'text/plain';
    }

    // Upsert (delete existing same-named file in output folder, then create)
    const blob = Utilities.newBlob(content, mimeType, fileName);
    const file = upsertFileInFolder(outputFolder, fileName, blob);
    fileUrls.push(file.getUrl());

    Logger.log(`Saved (upserted): ${fileName}`);
  });

  return fileUrls;
}

function getRawHtmlContent(message) {
  // Get email metadata
  const subject = message.getSubject();
  const date = message.getDate();
  const from = message.getFrom();
  const to = message.getTo();
  const cc = message.getCc();
  const bcc = message.getBcc();

  // Get raw HTML body - no cleaning
  const htmlBody = message.getBody();

  // Create simple HTML structure with metadata
  const html = `<!DOCTYPE html>
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

  return html;
}

function getRawTextContent(message) {
  // Get email metadata
  const subject = message.getSubject();
  const date = message.getDate();
  const from = message.getFrom();
  const to = message.getTo();
  const cc = message.getCc();
  const bcc = message.getBcc();

  // Get raw plain text body - no cleaning
  const plainBody = message.getPlainBody();

  // Create text format with metadata header
  const content = `EMAIL METADATA
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

  return content;
}

function saveSummarySpreadsheet(threads, outputFolder) {
  // Fixed (deterministic) name so we overwrite it each run
  const sheetName = `Matt_Levine_Summary`;

  // If an older copy exists in the output folder, remove it first
  deleteFilesByNameInFolder(outputFolder, sheetName);

  // Create new spreadsheet and move into output folder
  const ss = SpreadsheetApp.create(sheetName);
  const sheet = ss.getActiveSheet();
  DriveApp.getFileById(ss.getId()).moveTo(outputFolder);

  // Headers
  const headers = ['#', 'Date', 'Subject', 'From', 'To', 'Thread ID', 'Message ID', 'File Name'];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);

  // Format headers
  const headerRange = sheet.getRange(1, 1, 1, headers.length);
  headerRange.setFontWeight('bold');
  headerRange.setBackground('#4285f4');
  headerRange.setFontColor('white');

  // Add data
  const data = threads.map((thread, index) => {
    const messages = thread.getMessages();
    const latestMessage = messages[messages.length - 1];

    const subject = latestMessage.getSubject();
    const date = latestMessage.getDate();
    const dateStr = Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyy-MM-dd');
    const safeSubject = subject ? subject.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_').substring(0, 50) : 'No_Subject';
    const messageId = latestMessage.getId();
    const ext = CONFIG.FILE_FORMAT === 'html' ? 'html' : 'txt';
    const fileName = `${dateStr}_${safeSubject}_${messageId}.${ext}`;

    return [
      index + 1,
      date,
      subject,
      latestMessage.getFrom(),
      latestMessage.getTo(),
      thread.getId(),
      messageId,
      fileName
    ];
  });

  if (data.length > 0) {
    sheet.getRange(2, 1, data.length, headers.length).setValues(data);
  }

  // Format columns
  sheet.autoResizeColumns(1, headers.length);
  sheet.setColumnWidth(3, 300); // Subject
  sheet.setColumnWidth(4, 200); // From
  sheet.setColumnWidth(5, 200); // To
  sheet.setColumnWidth(8, 250); // File Name

  Logger.log(`Summary spreadsheet saved: ${ss.getUrl()}`);
  return ss.getUrl();
}

// ===== UTILITY FUNCTIONS =====
function getOrCreateFolder(folderName) {
  const folders = DriveApp.getFoldersByName(folderName);
  if (folders.hasNext()) {
    return folders.next();
  } else {
    return DriveApp.createFolder(folderName);
  }
}

/**
 * Upserts a file into the given folder by name: deletes any existing
 * same-named file(s) in that folder, then creates a new one from the blob.
 * Returns the created File.
 */
function upsertFileInFolder(folder, fileName, blob) {
  deleteFilesByNameInFolder(folder, fileName);
  blob.setName(fileName);
  return folder.createFile(blob);
}

/**
 * Deletes (trashes) all files with the given name that are inside `folder`.
 * Uses DriveApp.searchFiles with a v2 query scoped by parent folder ID.
 */
function deleteFilesByNameInFolder(folder, fileName) {
  const folderId = folder.getId();
  // Drive v2 uses 'title'. Also ensure proper escaping of single quotes.
  const safeName = fileName.replace(/'/g, "\\'");
  const query = `title = '${safeName}' and '${folderId}' in parents and trashed = false`;
  const it = DriveApp.searchFiles(query);
  while (it.hasNext()) {
    const f = it.next();
    f.setTrashed(true); // move to trash (safer than permanent delete)
  }
}

function escapeHtml(unsafe) {
  if (!unsafe) return '';
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ===== DEBUG FUNCTION =====
function debugEmailSearch() {
  Logger.log('=== DEBUGGING MATT LEVINE EMAIL SEARCH ===');

  const searchQueries = [
    `from:${CONFIG.SENDER_EMAIL} "${CONFIG.SEARCH_TERMS[0]}" ${CONFIG.SEARCH_LOCATION}`,
    `from:${CONFIG.SENDER_EMAIL} "${CONFIG.SEARCH_TERMS[1]}" ${CONFIG.SEARCH_LOCATION}`,
    `from:${CONFIG.SENDER_EMAIL} ${CONFIG.SEARCH_LOCATION}`,
    `"${CONFIG.SEARCH_TERMS[0]}" ${CONFIG.SEARCH_LOCATION}`,
    `"${CONFIG.SEARCH_TERMS[1]}" ${CONFIG.SEARCH_LOCATION}`
  ];

  searchQueries.forEach((query, index) => {
    Logger.log(`\n--- Search ${index + 1}: "${query}" ---`);
    try {
      const threads = GmailApp.search(query, 0, 3);
      Logger.log(`Found ${threads.length} threads`);

      threads.forEach((thread, threadIndex) => {
        const messages = thread.getMessages();
        const latestMessage = messages[messages.length - 1];
        Logger.log(`  ${threadIndex + 1}. "${latestMessage.getSubject()}"`);
        Logger.log(`     From: ${latestMessage.getFrom()}`);
        Logger.log(`     Date: ${latestMessage.getDate().toLocaleDateString()}`);
      });

    } catch (error) {
      Logger.log(`  Error: ${error.toString()}`);
    }
  });
}
