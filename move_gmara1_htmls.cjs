
const fs = require('fs');
const path = require('path');

const sourceDir = '/Users/yechiel/Developer/react/sfarim/public/shas/shastext/gmara1';
const backupDir = '/Users/yechiel/Developer/react/sfarim/backup files/gmara1';

function ensureDirectoryExistence(filePath) {
    var dirname = path.dirname(filePath);
    if (fs.existsSync(dirname)) {
        return true;
    }
    ensureDirectoryExistence(dirname);
    fs.mkdirSync(dirname);
}

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

if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir, { recursive: true });
}

console.log(`Moving HTML files from ${sourceDir} to ${backupDir}...`);

let count = 0;
walkDir(sourceDir, (filePath) => {
    if (path.extname(filePath) === '.html') {
        const relativePath = path.relative(sourceDir, filePath);
        const destPath = path.join(backupDir, relativePath);

        ensureDirectoryExistence(destPath);

        fs.renameSync(filePath, destPath);
        console.log(`Moved: ${relativePath}`);
        count++;
    }
});

console.log(`Moved ${count} HTML files to backup.`);
