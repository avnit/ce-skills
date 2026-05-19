/**
 * Creates the Add-on menu item in the Extensions dropdown.
 */
function onOpen(e) {
  DocumentApp.getUi()
    .createAddonMenu()
    .addItem('Open Formatter', 'showSidebar')
    .addToUi();
}

/**
 * Runs when the add-on is installed.
 */
function onInstall(e) {
  onOpen(e);
}

/**
 * Opens the sidebar UI.
 */
function showSidebar() {
  var html = HtmlService.createHtmlOutputFromFile('Sidebar')
      .setTitle('Codelab Formatter')
      .setWidth(300);
  DocumentApp.getUi().showSidebar(html);
}

/**
 * Helper to apply bold, inline code, and link styling within text elements
 */
function applyInlineStyles(element) {
  if (!element.editAsText) return;
  var textObj = element.editAsText();
  var text = textObj.getText();
  var match;
  var safety = 0; // Prevent infinite loops just in case
  
  // 1. Process Markdown Links ([text](url))
  var linkRegex = /\[([^\]]+)\]\(([^)]+)\)/;
  safety = 0;
  while ((match = text.match(linkRegex)) !== null && safety < 100) {
    var start = match.index;
    var linkText = match[1];
    var linkUrl = match[2];
    
    // Delete the full [text](url) string
    textObj.deleteText(start, start + match[0].length - 1);
    
    // Insert just the text and apply the link to it
    if (linkText.length > 0) {
      textObj.insertText(start, linkText);
      textObj.setLinkUrl(start, start + linkText.length - 1, linkUrl);
    }
    
    text = textObj.getText();
    safety++;
  }
  
  // 2. Process Bold (**text**)
  var boldRegex = /\*\*(.*?)\*\*/;
  safety = 0;
  while ((match = text.match(boldRegex)) !== null && safety < 100) {
    var start = match.index;
    var innerText = match[1];
    
    textObj.deleteText(start, start + 1); // remove first **
    var endAsterisks = start + innerText.length;
    textObj.deleteText(endAsterisks, endAsterisks + 1); // remove second **
    
    if (innerText.length > 0) {
      textObj.setBold(start, endAsterisks - 1, true);
    }
    text = textObj.getText();
    safety++;
  }
  
  // 3. Process Inline Code (`code`)
  var codeRegex = /`([^`]+)`/;
  safety = 0;
  while ((match = text.match(codeRegex)) !== null && safety < 100) {
    var start = match.index;
    var innerText = match[1];
    
    textObj.deleteText(start, start); // remove first `
    var endBacktick = start + innerText.length;
    textObj.deleteText(endBacktick, endBacktick); // remove second `
    
    if (innerText.length > 0) {
      textObj.setFontFamily(start, endBacktick - 1, 'Courier New');
      textObj.setBackgroundColor(start, endBacktick - 1, '#f8f9fa');
    }
    text = textObj.getText();
    safety++;
  }

  // 4. Process Plain Naked URLs (http://... or https://...)
  var plainUrlRegex = /https?:\/\/[^\s<)>\]]+/g;
  var urlMatch;
  while ((urlMatch = plainUrlRegex.exec(text)) !== null) {
    textObj.setLinkUrl(urlMatch.index, urlMatch.index + urlMatch[0].length - 1, urlMatch[0]);
  }
}

/**
 * Core parsing engine. Receives markdown from the sidebar,
 * parses Codelab elements, and maps them to Document styles.
 */
function processMarkdown(markdown) {
  var doc = DocumentApp.getActiveDocument();
  var body = doc.getBody();
  
  // Clear existing content to start fresh
  body.clear(); 

  // 1. Extract and Format Metadata (--- block)
  var metaRegex = /^---\n([\s\S]*?)\n---/;
  var metaMatch = markdown.match(metaRegex);
  if (metaMatch) {
    var metaText = metaMatch[1];
    var lines = metaText.split('\n');
    var tableCells = [];
    
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      var parts = line.split(':');
      if (parts.length >= 2) {
        var key = parts.shift().trim();
        var val = parts.join(':').trim();
        tableCells.push([key, val]);
      }
    }
    
    if (tableCells.length > 0) {
      body.appendTable(tableCells);
      body.appendParagraph('');
    }
    // Remove metadata from markdown to process the rest
    markdown = markdown.replace(metaRegex, '').trim();
  }

  // 2. Protect Code Blocks to prevent them from being split
  var codeBlocks = [];
  markdown = markdown.replace(/```([a-z]*)\n([\s\S]*?)```/gi, function(match, lang, content) {
    codeBlocks.push({ lang: lang ? lang.trim().toLowerCase() : '', content: content.trim() });
    return '\n\n%%%CODE_BLOCK_' + (codeBlocks.length - 1) + '%%%\n\n';
  });

  // 3. Protect Asides (Info/Warning boxes)
  var asides = [];
  var asideRegex = /(?:^|\n)>[\s\u00A0]*aside[\s\u00A0]+(positive|negative)([\s\S]*?)(?=\n\n|\n$)/gi;
  markdown = markdown.replace(asideRegex, function(match, type, content) {
    content = content.replace(/(^|\n|\s+)>[\s\u00A0]*/g, '$1').trim();
    asides.push({ type: type.toLowerCase(), content: content });
    return '\n\n%%%ASIDE_' + (asides.length - 1) + '%%%\n\n';
  });

  // 4. Normalize Spacing 
  // Ensure headings and durations are on their own standalone blocks so lists don't get swallowed
  markdown = markdown.replace(/^(#{1,6}\s.*)$/gm, '\n\n$1\n\n');
  markdown = markdown.replace(/^(Duration:\s.*)$/gm, '\n\n$1\n\n');

  // 5. Process Remaining Blocks
  var blocks = markdown.split(/\n\n+/);
  var isFirstStep = true;
  var lastListItem = null; // Track the first list item object to continue numbering across code blocks

  for (var j = 0; j < blocks.length; j++) {
    var block = blocks[j].trim();
    if (!block) continue;

    var p; // Element reference to apply inline styles
    
    // Handle Code Blocks
    if (block.indexOf('%%%CODE_BLOCK_') === 0) {
       var codeIdx = parseInt(block.match(/%%%CODE_BLOCK_(\d+)%%%/)[1]);
       var codeObj = codeBlocks[codeIdx];
       var table = body.appendTable([['']]); 
       var cell = table.getCell(0,0);
       cell.setText(codeObj.content);
       cell.setBackgroundColor('#f8f9fa'); // Light gray for code
       
       var isConsole = (codeObj.lang === 'console' || codeObj.lang === 'sh' || codeObj.lang === 'bash' || codeObj.lang === 'terminal');
       cell.editAsText().setFontFamily(isConsole ? 'Consolas' : 'Courier New').setFontSize(10);
       
       body.appendParagraph('');
       continue; 
    }
    
    // Handle Asides (Positive/Negative)
    else if (block.indexOf('%%%ASIDE_') === 0) {
       var asideIdx = parseInt(block.match(/%%%ASIDE_(\d+)%%%/)[1]);
       var aside = asides[asideIdx];
       var asideTable = body.appendTable([['']]); 
       var asideCell = asideTable.getCell(0,0);
       asideCell.setText(aside.content);
       
       if (aside.type === 'positive') {
         asideCell.setBackgroundColor('#d9ead3'); // Light green 3
       } else {
         asideCell.setBackgroundColor('#fce5cd'); // Light orange 3
       }
       
       applyInlineStyles(asideCell);
       body.appendParagraph('');
       continue;
    }
    
    // Handle Title (# )
    else if (block.match(/^#\s(.*)/)) {
       var titleText = block.match(/^#\s(.*)/)[1].replace(/^\d+\.\s*/, '');
       p = body.appendParagraph(titleText).setHeading(DocumentApp.ParagraphHeading.TITLE);
       applyInlineStyles(p);
    }
    
    // Handle Heading 1 (Steps - ## ) & Page Breaks
    else if (block.match(/^##\s(.*)/)) {
       var stepText = block.match(/^##\s(.*)/)[1].replace(/^\d+\.\s*/, '');
       if (!isFirstStep) {
         body.appendPageBreak();
       }
       isFirstStep = false;
       p = body.appendParagraph(stepText).setHeading(DocumentApp.ParagraphHeading.HEADING1);
       applyInlineStyles(p);
    }

    // Handle Heading 2 (Sub-steps - ### )
    else if (block.match(/^###\s(.*)/)) {
       var h2Text = block.match(/^###\s(.*)/)[1].replace(/^\d+\.\s*/, '');
       p = body.appendParagraph(h2Text).setHeading(DocumentApp.ParagraphHeading.HEADING2);
       applyInlineStyles(p);
    }
    
    // Handle Heading 3 (Sub-steps - #### )
    else if (block.match(/^####\s(.*)/)) {
       var h3Text = block.match(/^####\s(.*)/)[1].replace(/^\d+\.\s*/, '');
       p = body.appendParagraph(h3Text).setHeading(DocumentApp.ParagraphHeading.HEADING3);
       applyInlineStyles(p);
    }
    
    // Handle Duration Text
    else if (block.match(/^Duration:\s(.*)/i)) {
       p = body.appendParagraph(block);
       var textElem = p.editAsText();
       textElem.setItalic(true);
       textElem.setForegroundColor('#5f6368'); // Set text color to gray
       applyInlineStyles(p);
    }
    
    // Handle standard text & Lists
    else {
       var lines = block.split('\n');
       var currentText = [];
       var currentType = 'paragraph'; 
       var currentNumber = null;
       
       // Helper to commit the current line group as a Doc element
       var flush = function() {
         if (currentText.length > 0) {
           var text = currentText.join(' ');
           var elem;
           if (currentType === 'bullet') {
             elem = body.appendListItem(text).setGlyphType(DocumentApp.GlyphType.BULLET);
           } else if (currentType === 'number') {
             elem = body.appendListItem(text).setGlyphType(DocumentApp.GlyphType.NUMBER);
             
             // Link lists together across code blocks
             if (currentNumber === 1) {
               lastListItem = elem; // Store the actual list item object
             } else if (lastListItem !== null) {
               elem.setListId(lastListItem); // Attach to the previous list using the list item object
             }

           } else {
             elem = body.appendParagraph(text);
           }
           applyInlineStyles(elem);
           currentText = [];
         }
       };

       for (var k = 0; k < lines.length; k++) {
         var line = lines[k].trim();
         if (!line) continue;
         
         // Match Markdown bullets (*) or (-) and numbering (1.)
         var bulletMatch = line.match(/^[\*\-]\s+(.*)/);
         var numMatch = line.match(/^(\d+)\.\s+(.*)/); // Capture the actual number
         
         if (bulletMatch) {
           flush(); // Print previous text
           currentType = 'bullet';
           currentText.push(bulletMatch[1]);
         } else if (numMatch) {
           flush(); // Print previous text
           currentType = 'number';
           currentNumber = parseInt(numMatch[1], 10);
           currentText.push(numMatch[2]);
         } else {
           // Treat as a continuation of the same paragraph or bullet
           currentText.push(line);
         }
       }
       flush(); // Print remainder
    }
  }

  // Cleanup single empty paragraph at the top of document
  var firstChild = body.getChild(0);
  if (firstChild.getType() === DocumentApp.ElementType.PARAGRAPH && firstChild.getText() === "") {
    firstChild.removeFromParent();
  }
  
  return "Document formatted successfully!";
}
