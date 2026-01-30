
const fs = require('fs');
const path = require('path');

const targetDir = '/Users/yechiel/Developer/react/sfarim/public/shas/shastext/gmara1';

function walkDir(dir, callback) {
    fs.readdirSync(dir).forEach(f => {
        let dirPath = path.join(dir, f);
        let isDirectory = fs.statSync(dirPath).isDirectory();
        if (isDirectory) {
            walkDir(dirPath, callback);
        } else {
            callback(path.join(dir, f));
        }
    });
}

console.log('Starting Gmara1 HTML conversion in ' + targetDir);

walkDir(targetDir, (filePath) => {
    if (path.extname(filePath) === '.html') {
        try {
            let content = fs.readFileSync(filePath, 'utf8');
            // Escape special characters for JS string
            content = content.replace(/\\/g, '\\\\')
                .replace(/"/g, '\\"')
                .replace(/\n/g, '\\n')
                .replace(/\r/g, '');

            const jsContent = `loadedGmaraText("${content}");`;
            const jsFilePath = filePath.replace('.html', '.js');

            fs.writeFileSync(jsFilePath, jsContent);
            console.log(`Converted: ${filePath} -> ${jsFilePath}`);
        } catch (e) {
            console.error(`Error converting ${filePath}:`, e);
        }
    }
});

console.log('Conversion complete.');
