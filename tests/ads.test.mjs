import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';

const source = readFileSync(new URL('../ads.js', import.meta.url), 'utf8');
const accepted = {cmpStatus:'loaded', eventStatus:'useractioncomplete', cmpId:123,
  tcString:'simulated-test-only', vendor:{consents:{755:true}}, purpose:{consents:{1:true,3:true,4:true}}};
async function environment({enabled=true, hostname='www.golguess.com.br', game=null}={}) {
  const ins = {dataset:{}};
  const slot = {hidden:true,dataset:{},querySelector:()=>ins,getBoundingClientRect:()=>({top:1200,bottom:1320})};
  const scripts = [], observers = [], intervals = [], resizes = [];
  let callback;
  const window = {addEventListener(){},__tcfapi(command,version,cb) { callback=cb; }};
  const document = {getElementById(){return game;},querySelector(selector){return selector==='dialog[open]' ? null : slot;},
    querySelectorAll(){return [];},createElement(){return {};},head:{append(script){scripts.push(script);script.onload();}}};
  vm.runInNewContext(source,{window,document,location:{hostname},innerHeight:900,scrollY:0,
    fetch:async()=>({ok:true,json:async()=>({adsEnabled:enabled,cmpId:'123'})}),
    MutationObserver:class {constructor(cb){observers.push(cb);} observe(){}},
    ResizeObserver:class {constructor(cb){resizes.push(cb);} observe(){}},
    setInterval(cb){intervals.push(cb);return 1;},clearInterval(){},setTimeout(){}});
  await new Promise(resolve=>setImmediate(resolve));
  intervals.forEach(cb=>cb());
  return {slot,scripts,ins,observers,resizes,window,consent(tc,success=true){callback?.(tc,success);}};
}
test('No ads for missing CMP, denied, malformed or unconfigured consent in any region', async()=>{
  for(const region of ['BR','DE','GB','CH','US','unknown']) {
    const env=await environment(); env.window.golguessAds.setEligible(true);
    for(const tc of [{}, {...accepted,tcString:''}, {...accepted,cmpId:999},
      {...accepted,gdprApplies:false,vendor:{consents:{}}}, {...accepted,purpose:{consents:{1:true}}}]) {
      env.consent({...tc,region}); assert.equal(env.scripts.length,0); assert.equal(env.slot.hidden,true);
    }
  }
});
test('One request with consent and content; no refresh after result/mode changes; withdrawal hides', async()=>{
  const env=await environment(); env.consent(accepted);
  assert.equal(env.scripts.length,0);
  env.window.golguessAds.setEligible(true);
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(env.scripts.length,1); assert.equal(env.window.adsbygoogle.length,1);
  env.window.golguessAds.setEligible(false); assert.equal(env.slot.hidden,true);
  env.window.golguessAds.setEligible(true); assert.equal(env.scripts.length,1);
  env.consent({...accepted,vendor:{consents:{}}}); assert.equal(env.slot.hidden,true);
});
test('Unfilled collapses safely and cannot be requested again', async()=>{
  const env=await environment(); env.consent(accepted); env.window.golguessAds.setEligible(true);
  await new Promise(resolve=>setImmediate(resolve));
  env.ins.dataset.adStatus='unfilled'; env.observers[0]();
  assert.equal(env.slot.hidden,true);
  env.window.golguessAds.setEligible(true); assert.equal(env.slot.hidden,true);
  assert.equal(env.window.adsbygoogle.length,1);
});
test('Preview/local hosts and disabled configuration never request Google', async()=>{
  for(const options of [{hostname:'localhost'}, {hostname:'preview.vercel.app'}, {enabled:false}]) {
    const env=await environment(options);env.consent(accepted);env.window.golguessAds.setEligible(true);
    assert.equal(env.scripts.length,0);
  }
});
test('An ad cannot rise into former controls when a smaller game mode is selected', async()=>{
  let height=1000;
  const game={style:{},getBoundingClientRect:()=>({height})};
  const env=await environment({game});
  env.consent(accepted);env.window.golguessAds.setEligible(true);
  assert.equal(game.style.minHeight,'1000px');
  height=500;env.resizes[0]();assert.equal(game.style.minHeight,'1000px');
  height=1200;env.resizes[0]();assert.equal(game.style.minHeight,'1200px');
});
