import fs from 'node:fs';

// One-shot P0 migration: language persistence must never crash the game.
const path = 'COFFEE_BATTLES.html';
let src = fs.readFileSync(path, 'utf8');

if (src.includes('storageSafe:{')) {
  console.log('Fail-safe storage adapter already present.');
  process.exit(0);
}

const detectBefore = `  detect(){
    const saved=localStorage.getItem(this.STORAGE_KEY);
    if(saved&&I18N.languages[saved])return saved;
    return 'en';
  },`;

const detectAfter = `  storageSafe:{
    memory:new Map(),
    get(key){
      try{
        const value=localStorage.getItem(key);
        if(value!==null)this.memory.set(key,value);
        return value;
      }catch(_){
        return this.memory.get(key)??null;
      }
    },
    set(key,value){
      const text=String(value);
      this.memory.set(key,text);
      try{
        localStorage.setItem(key,text);
        return true;
      }catch(_){
        return false;
      }
    }
  },
  detect(){
    const saved=this.storageSafe.get(this.STORAGE_KEY);
    if(saved&&I18N.languages[saved])return saved;
    return 'en';
  },`;

const setBefore = `    if(persist)localStorage.setItem(this.STORAGE_KEY,this.current);`;
const setAfter = `    if(persist)this.storageSafe.set(this.STORAGE_KEY,this.current);`;

if (!src.includes(detectBefore)) throw new Error('I18N detect localStorage target not found');
if (!src.includes(setBefore)) throw new Error('I18N set localStorage target not found');

src = src.replace(detectBefore, detectAfter).replace(setBefore, setAfter);
fs.writeFileSync(path, src);
console.log('Fail-safe language storage adapter applied.');
