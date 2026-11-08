import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/fonts';

const serif = 'Cormorant Garamond';
const sans = 'Montserrat';
loadFont({family: serif, url: staticFile('fonts/cormorant-garamond-latin-600-normal.woff2'), weight: '600'});
for (const w of ['500', '600', '700']) {
  loadFont({family: sans, url: staticFile(`fonts/montserrat-latin-${w}-normal.woff2`), weight: w});
}

export const FPS = 30;
const VIDEO_SECONDS = 10;
const EXTRA_END_SECONDS = 2.5;
export const TOTAL_FRAMES = Math.round((VIDEO_SECONDS + EXTRA_END_SECONDS) * FPS);

const SAGE = '#B9CFAE';
const CREAM = '#F6E3D3';
const INK = '#1E1B15';

const s = (sec: number) => Math.round(sec * FPS);

// Cuts detected in the source video (seconds).
const SCENES: {from: number; to: number; eyebrow: string; title: string}[] = [
  {from: 1.25, to: 2.46, eyebrow: 'Paso 1', title: 'Velas tipo postre'},
  {from: 2.46, to: 3.58, eyebrow: 'Paso 2', title: 'Aromas naturales'},
  {from: 3.58, to: 4.75, eyebrow: 'Paso 3', title: 'Moldes y acabados'},
  {from: 4.75, to: 5.96, eyebrow: 'Resultado', title: 'Piezas únicas'},
  {from: 5.96, to: 7.42, eyebrow: 'Clases', title: 'En grupos pequeños'},
  {from: 7.42, to: 8.75, eyebrow: 'Al final', title: '¡Te llevas tus creaciones!'},
];
const END_CARD_START = 8.75;
const CUTS = [0, 1.25, 2.46, 3.58, 4.75, 5.96, 7.42, 8.75, 10];

/** Gentle push-in that restarts on every cut, so static AI shots feel alive. */
const useSceneZoom = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  let i = 0;
  while (i < CUTS.length - 2 && t >= CUTS[i + 1]) i++;
  const p = (t - CUTS[i]) / (CUTS[i + 1] - CUTS[i]);
  return interpolate(Math.min(p, 1), [0, 1], [1.0, 1.06]);
};

const BaseVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const scale = useSceneZoom();
  const volume = interpolate(frame, [s(9.2), s(VIDEO_SECONDS)], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{transform: `scale(${scale})`}}>
      <OffthreadVideo
        src={staticFile('original.mp4')}
        volume={volume}
        style={{width: '100%', height: '100%', objectFit: 'cover'}}
      />
    </AbsoluteFill>
  );
};

const BottomShade: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'linear-gradient(180deg, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0) 18%, rgba(0,0,0,0) 45%, rgba(20,16,10,0.75) 82%, rgba(20,16,10,0.8) 100%)',
    }}
  />
);

/** Opening hook – first 1.25 s, top of frame (below IG's header UI). */
const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = ['¿Quieres', 'crear', 'tus', 'propias', 'velas?'];
  const out = interpolate(frame, [s(1.05), s(1.25)], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const tag = spring({frame, fps, config: {damping: 14}});
  return (
    <AbsoluteFill
      style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 430, opacity: out}}
    >
      <div
        style={{
          fontFamily: sans,
          fontWeight: 600,
          fontSize: 30,
          letterSpacing: 8,
          color: INK,
          background: SAGE,
          padding: '12px 28px',
          borderRadius: 999,
          transform: `scale(${tag})`,
          marginBottom: 28,
        }}
      >
        TALLER ARTESANAL
      </div>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          width: 900,
          gap: '0 22px',
        }}
      >
        {words.map((w, i) => {
          const p = spring({frame: frame - 3 - i * 3, fps, config: {damping: 13, mass: 0.6}});
          return (
            <span
              key={w}
              style={{
                fontFamily: serif,
                fontWeight: 600,
                fontSize: 104,
                lineHeight: 1.05,
                color: 'white',
                textShadow: '0 6px 30px rgba(0,0,0,0.55)',
                opacity: p,
                transform: `translateY(${(1 - p) * 40}px)`,
                display: 'inline-block',
              }}
            >
              {w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Lower-third caption for each scene; sits above IG's bottom UI. */
const Caption: React.FC<{eyebrow: string; title: string; duration: number}> = ({
  eyebrow,
  title,
  duration,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 15, mass: 0.7}});
  const exit = interpolate(frame, [duration - 5, duration], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const line = spring({frame: frame - 4, fps, config: {damping: 20}});
  return (
    <AbsoluteFill
      style={{justifyContent: 'flex-end', alignItems: 'flex-start', padding: '0 70px 420px'}}
    >
      <div
        style={{
          opacity: enter * exit,
          transform: `translateX(${(1 - enter) * -60}px)`,
          background: 'rgba(30,27,21,0.55)',
          backdropFilter: 'blur(14px)',
          borderLeft: `6px solid ${SAGE}`,
          borderRadius: 20,
          padding: '28px 40px 34px',
        }}
      >
        <div
          style={{
            fontFamily: sans,
            fontWeight: 700,
            fontSize: 34,
            letterSpacing: 7,
            textTransform: 'uppercase',
            color: SAGE,
            textShadow: '0 2px 12px rgba(0,0,0,0.6)',
          }}
        >
          {eyebrow}
        </div>
        <div
          style={{
            height: 5,
            width: 120 * line,
            background: CREAM,
            borderRadius: 3,
            margin: '14px 0 18px',
          }}
        />
        <div
          style={{
            fontFamily: serif,
            fontWeight: 600,
            fontSize: 92,
            lineHeight: 1.02,
            color: 'white',
            maxWidth: 820,
            textShadow: '0 4px 20px rgba(0,0,0,0.5)',
          }}
        >
          {title}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Call to action under the brand title of the source end card. */
const CallToAction: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const btn = spring({frame, fps, config: {damping: 12}});
  const sub = spring({frame: frame - 8, fps, config: {damping: 18}});
  const pulse = 1 + 0.03 * Math.sin((frame / fps) * Math.PI * 2);
  return (
    <AbsoluteFill style={{alignItems: 'center', paddingTop: 1300}}>
      <div
        style={{
          fontFamily: sans,
          fontWeight: 700,
          fontSize: 44,
          letterSpacing: 3,
          color: INK,
          background: SAGE,
          padding: '28px 64px',
          borderRadius: 999,
          boxShadow: '0 12px 40px rgba(185,207,174,0.25)',
          transform: `scale(${btn * (frame > 20 ? pulse : 1)})`,
        }}
      >
        RESERVA TU LUGAR
      </div>
      <div
        style={{
          marginTop: 36,
          fontFamily: sans,
          fontWeight: 500,
          fontSize: 34,
          letterSpacing: 2,
          color: CREAM,
          opacity: sub,
          transform: `translateY(${(1 - sub) * 20}px)`,
        }}
      >
        Cupos limitados · Link en la bio
      </div>
    </AbsoluteFill>
  );
};

const FrozenEndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, s(EXTRA_END_SECONDS)], [1.0, 1.03]);
  return (
    <AbsoluteFill style={{transform: `scale(${scale})`}}>
      <Img src={staticFile('endframe.png')} style={{width: '100%', height: '100%'}} />
    </AbsoluteFill>
  );
};

export const InstagramReel: React.FC = () => {
  const frame = useCurrentFrame();
  const fadeIn = interpolate(frame, [0, 6], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{backgroundColor: INK, opacity: fadeIn}}>
      <Sequence durationInFrames={s(VIDEO_SECONDS)}>
        <BaseVideo />
      </Sequence>
      <Sequence from={s(VIDEO_SECONDS)}>
        <FrozenEndCard />
      </Sequence>
      <Sequence durationInFrames={s(END_CARD_START)}>
        <BottomShade />
      </Sequence>
      <Sequence durationInFrames={s(1.25)}>
        <Hook />
      </Sequence>
      {SCENES.map((sc) => {
        const dur = s(sc.to) - s(sc.from);
        return (
          <Sequence key={sc.title} from={s(sc.from)} durationInFrames={dur}>
            <Caption eyebrow={sc.eyebrow} title={sc.title} duration={dur} />
          </Sequence>
        );
      })}
      <Sequence from={s(9.3)}>
        <CallToAction />
      </Sequence>
    </AbsoluteFill>
  );
};
