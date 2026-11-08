import {Composition} from 'remotion';
import {InstagramReel, TOTAL_FRAMES, FPS} from './InstagramReel';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="InstagramReel"
    component={InstagramReel}
    durationInFrames={TOTAL_FRAMES}
    fps={FPS}
    width={1080}
    height={1920}
  />
);
