import React from 'react';
import {Composition, AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring} from 'remotion';

const palette = {bg:'#070b1b', panel:'#101a35', cyan:'#5ee7ff', violet:'#b69cff', yellow:'#ffd166', text:'#f4f7fb', muted:'#aab6cf', red:'#ff7aa8'};

function Background() {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const drift = interpolate(frame, [0, durationInFrames], [-80, 80]);
  return <AbsoluteFill style={{background:`radial-gradient(circle at ${50 + drift/30}% 25%, #1a2860 0%, ${palette.bg} 52%, #03050d 100%)`}}>
    <div style={{position:'absolute', inset:0, opacity:.16, backgroundImage:'linear-gradient(rgba(94,231,255,.18) 1px, transparent 1px), linear-gradient(90deg, rgba(94,231,255,.18) 1px, transparent 1px)', backgroundSize:'64px 64px', transform:`translateX(${drift}px)`}} />
  </AbsoluteFill>;
}

function Header({topic, profile}) {
  return <div style={{position:'absolute', top:42, left:58, right:58, display:'flex', justifyContent:'space-between', fontFamily:'Arial', letterSpacing:2, color:palette.cyan, fontSize:22, fontWeight:700}}>
    <span>MASTER PEDAGOGY · MPVE · CINEMATIC</span><span>{profile || 'ADAPTIVE PHYSICS'}</span>
    <div style={{position:'absolute', top:44, left:0, color:palette.text, fontSize:54, letterSpacing:0}}>{topic}</div>
  </div>;
}

function FadeIn({children, start=0, duration=18, style={}}) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [start, start+duration], [0, 1], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const y = interpolate(frame, [start, start+duration], [24, 0], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  return <div style={{opacity, transform:`translateY(${y}px)`, ...style}}>{children}</div>;
}

function Equation({text}) {
  return <div style={{fontFamily:'Georgia', color:palette.yellow, fontSize:42, fontWeight:700, padding:'14px 20px', borderLeft:`4px solid ${palette.yellow}`, background:'rgba(255,209,102,.08)'}}>{text}</div>;
}

function PhysicsVisual({visual, progress}) {
  const x = 130 + progress * 380;
  const rolling = visual?.kind === 'rolling';
  const floatation = visual?.kind === 'floatation';
  if (floatation) return <div style={{position:'relative', width:620, height:430}}>
    <div style={{position:'absolute', left:30, right:20, top:250, height:170, background:'linear-gradient(#123c72,#0a2447)', borderTop:`4px solid ${palette.cyan}`, opacity:.9}} />
    <div style={{position:'absolute', left:220, top:180 - progress*15, width:180, height:120, borderRadius:'45% 45% 35% 35%', background:'#e8aa65', border:`5px solid ${palette.yellow}`, transform:`rotate(${progress*3-1.5}deg)`}} />
    <div style={{position:'absolute', left:305, top:110, color:palette.cyan, fontSize:34}}>↑ F<sub>B</sub></div>
    <div style={{position:'absolute', left:320, top:350, color:palette.red, fontSize:34}}>↓ mg</div>
  </div>;
  if (rolling) return <div style={{position:'relative', width:620, height:430}}>
    <div style={{position:'absolute', left:40, top:320, width:520, height:10, background:palette.cyan, transform:'rotate(-13deg)', transformOrigin:'left'}} />
    <div style={{position:'absolute', left:x, top:215 - progress*50, width:118, height:118, borderRadius:'50%', background:'#173e62', border:`6px solid ${palette.red}`, transform:`rotate(${progress*720}deg)`}}>
      <div style={{position:'absolute', left:53, top:12, width:5, height:94, background:palette.yellow}} /><div style={{position:'absolute', left:12, top:53, width:94, height:5, background:palette.yellow}} />
    </div>
    <div style={{position:'absolute', left:x+140, top:165-progress*50, color:palette.violet, fontSize:32}}>ω</div><div style={{position:'absolute', left:x-70, top:340-progress*50, color:palette.cyan, fontSize:30}}>v</div>
  </div>;
  return <div style={{position:'relative', width:620, height:430}}><div style={{position:'absolute', left:x, top:220-progress*60, width:120, height:120, borderRadius:'50%', background:'#173e62', border:`6px solid ${palette.cyan}`}} /><div style={{position:'absolute', left:x+150, top:210-progress*60, color:palette.cyan, fontSize:28}}>concept flow →</div></div>;
}

function Scene({scene, topic}) {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const enter = spring({frame, fps, config:{damping:18, stiffness:110}});
  return <AbsoluteFill style={{padding:'150px 58px 50px', fontFamily:'Arial', color:palette.text}}>
    <FadeIn style={{display:'flex', gap:42, height:'100%'}}>
      <div style={{width:650, display:'flex', alignItems:'center', justifyContent:'center'}}><PhysicsVisual visual={scene.visual || {}} progress={progress} /></div>
      <div style={{width:500, alignSelf:'center', transform:`scale(${.94 + enter*.06})`}}>
        <div style={{fontSize:25, color:palette.violet, textTransform:'uppercase', letterSpacing:3, marginBottom:18}}>{scene.label || 'KEY IDEA'}</div>
        <div style={{fontSize:34, lineHeight:1.15, fontWeight:700, marginBottom:22}}>{scene.title || topic}</div>
        <div style={{fontSize:23, lineHeight:1.4, color:palette.muted}}>{scene.explanation || ''}</div>
        {scene.equation ? <div style={{marginTop:28}}><Equation text={scene.equation} /></div> : null}
      </div>
    </FadeIn>
  </AbsoluteFill>;
}

function Captions({words=[]}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const now = frame / fps * 1000;
  const active = words.find(w => w.start_ms <= now && now < w.end_ms);
  if (!words.length) return null;
  return <div style={{position:'absolute', left:140, right:140, bottom:54, display:'flex', justifyContent:'center', gap:14, padding:'12px 20px', borderRadius:12, background:'rgba(3,5,13,.84)', fontFamily:'Arial', fontSize:30, fontWeight:700}}>
    {words.map((word, i) => <span key={i} style={{color:active === word ? palette.yellow : (word.start_ms > now ? '#71809e' : palette.text)}}>{word.text}</span>)}
  </div>;
}

function MPVE({topic='Physics', profile='', scenes=[], captionWords=[]}) {
  const {durationInFrames, fps} = useVideoConfig();
  const safeScenes = scenes.length ? scenes : [{title:'MPVE', explanation:'A focused visual explanation.', visual:{kind:'generic'}}];
  return <AbsoluteFill><Background/><Header topic={topic} profile={profile}/>
    {safeScenes.map((scene, index) => { const start = Math.round((scene.start_seconds || 0) * fps); const duration = Math.max(1, Math.round((scene.duration_seconds || durationInFrames/fps) * fps)); return <Sequence key={scene.id || index} from={start} durationInFrames={duration}><Scene scene={scene} topic={topic}/></Sequence>; })}
    <Captions words={captionWords}/>
  </AbsoluteFill>;
}

export const RemotionRoot = () => <Composition id="MPVE" component={MPVE} durationInFrames={450} fps={30} width={1920} height={1080} defaultProps={{topic:'Physics', scenes:[]}} />;
