// Documentation remains accessible without connecting or disclosing a ticket cause.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/desktop.html','utf8');
const start=html.indexOf('const trainingDocuments=[');
const end=html.indexOf('\nfunction documentationApp',start);
assert(start>=0&&end>start);
const context={};vm.createContext(context);
vm.runInContext(html.slice(start,end)+'\nglobalThis.documents=trainingDocuments;',context);
const article=context.documents.find(d=>d.id==='ftp-access');
assert(article,'FTP documentation exists');
assert(article.paragraphs.join(' ').includes('Formation!2026'));
assert(article.paragraphs.join(' ').includes('FTP_AUTHENTICATION_FAILED'));
assert(article.paragraphs.join(' ').includes('NETWORK_UNKNOWN'));
assert(article.paragraphs.join(' ').includes('FTP_DATA_BLOCKED'));
const client=html.slice(html.indexOf('function ftpClient(){'),html.indexOf('function ftpAdmin(){'));
assert(client.includes("button('Aide connexion FTP',helpPanel,()=>documentationApp('ftp-access'))"));
assert(!client.includes("password.value='Formation!2026'"),'Help must not fill credentials automatically');
console.log('FTP help: reference credentials, ambiguous refusal, network/data distinction and documentation link OK');
