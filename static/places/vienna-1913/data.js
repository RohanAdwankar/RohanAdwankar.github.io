// Vienna, 1913. Where everybody was, and what they were doing there.

export default {
  id: 'vienna-1913',
  assets: '/places/vienna-1913',
  hint: 'Drag him onto a pin.',
  map: {
    width: 1000, height: 640,
    draw(m) {
      // The Danube Canal cuts the old city off to the north-east, the
      // Ringstraße loops it, and the Wien river slips in from the south-west.
      m.water('M 300 0 C 380 40 460 60 540 120 C 620 180 700 240 760 330 C 800 390 860 440 900 520 C 930 580 960 610 1000 640 L 1000 600 C 950 560 920 520 890 470 C 850 400 810 350 760 290 C 690 210 610 150 540 100 C 470 50 400 20 330 0 Z');
      m.label('Donaukanal', 690, 232, 'water');
      m.water('M 0 470 C 60 470 120 490 180 500 C 240 510 280 505 320 520 C 360 535 380 560 400 600 L 400 640 L 380 640 C 366 600 350 560 310 545 C 270 530 230 530 180 522 C 120 512 60 496 0 492 Z');
      m.label('Wien', 110, 462, 'water');
      // Parks.
      m.park('M 560 330 C 600 320 640 340 650 380 C 655 420 620 450 580 450 C 545 445 525 410 530 375 C 535 350 545 335 560 330 Z');
      m.label('Stadtpark', 566, 395, 'park');
      m.park('M 340 240 L 410 230 L 430 300 L 360 315 Z');
      m.label('Volksgarten', 352, 280, 'park');
      m.park('M 360 330 L 470 330 L 480 400 L 380 410 Z');
      m.label('Burggarten', 396, 375, 'park');
      m.park('M 700 470 L 820 450 L 860 560 L 740 580 Z');
      m.label('Belvedere gardens', 730, 520, 'park');
      m.park('M 60 60 L 200 40 L 230 130 L 90 150 Z');
      m.label('Allgemeines Krankenhaus', 80, 105, 'park');
      // Blocks: a loose texture of city, denser inside the Ring.
      const blocks = [
        [430,190,60,40],[500,180,70,45],[580,210,60,40],[460,240,50,40],[520,240,60,35],[600,265,55,40],
        [440,300,40,30],[500,290,50,45],[560,290,50,30],[470,350,40,40],[520,345,50,45],[610,320,40,35],
        [250,160,60,40],[180,180,60,40],[120,200,60,45],[240,220,70,40],[150,260,70,45],[230,290,80,45],
        [120,330,80,50],[220,350,80,50],[130,400,80,40],[230,420,70,40],[300,430,60,40],
        [660,120,60,40],[730,150,60,45],[720,80,70,40],[800,110,60,40],[820,190,60,50],[880,140,60,40],
        [440,470,70,40],[520,470,80,45],[610,470,70,40],[450,530,80,40],[540,530,90,45],[640,540,60,40],
        [480,590,80,40],[580,600,80,35],[300,500,60,40],[320,560,70,45],[200,540,70,40],[100,560,80,40],
        [880,300,60,40],[900,380,60,40],[860,240,50,40],[300,80,60,40],[380,100,70,40],[250,80,50,40],
        [560,60,60,40],[620,40,70,40],[480,60,60,40],[40,300,60,40],[30,380,60,40],[40,220,60,40],
      ];
      for (const [x, y, w, h] of blocks) m.block(`M ${x} ${y} h ${w} v ${h} h ${-w} Z`);
      // Streets.
      m.road('M 330 150 C 420 130 520 130 610 150 C 690 170 720 250 700 330 C 690 400 640 450 560 470 C 480 490 400 470 360 420 C 320 370 300 300 320 230 C 325 200 328 170 330 150 Z', 'ring');
      m.label('Ringstraße', 372, 452, 'road');
      m.road('M 480 130 L 470 330', 'major');
      m.road('M 620 150 L 560 330', 'major');
      m.road('M 700 330 L 470 330 L 360 420', 'major');
      m.road('M 60 30 L 330 150', 'major');
      m.road('M 0 250 L 320 230', 'major');
      m.road('M 0 380 L 360 420 L 330 640', 'major');
      m.road('M 360 420 L 280 640', 'minor');
      m.road('M 560 470 L 590 640', 'major');
      m.road('M 640 450 L 760 600', 'major');
      m.road('M 700 330 L 880 260', 'major');
      m.road('M 610 150 L 660 40', 'major');
      m.road('M 400 0 L 330 150', 'major');
      m.road('M 700 330 L 860 400', 'minor');
      m.road('M 780 0 L 740 250', 'minor');
      m.road('M 100 480 L 460 490 L 640 500', 'minor');
      m.road('M 0 560 L 300 550 L 400 640', 'minor');
      m.road('M 150 150 L 200 400', 'minor');
      m.road('M 240 130 L 250 420', 'minor');
      m.road('M 60 200 L 80 460', 'minor');
      m.road('M 430 190 L 400 300', 'minor');
      m.road('M 540 170 L 520 330', 'minor');
      m.road('M 400 220 L 640 250', 'minor');
      m.road('M 380 280 L 660 300', 'minor');
      m.road('M 440 410 L 640 380', 'minor');
      m.road('M 800 60 L 1000 120', 'minor');
      m.road('M 820 470 L 1000 430', 'minor');
      m.road('M 640 620 L 1000 540', 'minor');
      m.road('M 0 60 L 60 30 L 200 0', 'rail');
      m.label('Herrengasse', 440, 265, 'road');
      m.label('Berggasse', 250, 150, 'road');
      m.label('Alsergrund', 150, 320, 'area');
      m.label('Innere Stadt', 520, 420, 'area');
      m.label('Leopoldstadt', 790, 90, 'area');
      m.label('Landstraße', 850, 350, 'area');
      m.label('Wieden', 470, 570, 'area');
      m.label('Josefstadt', 150, 440, 'area');
      m.label('Mariahilf', 200, 600, 'area');
    },
  },

  pins: [
    {
      id: 'cafe-central', label: 'Café Central', x: 455, y: 268,
      scene: {
        title: 'Café Central', subtitle: 'Herrengasse 14, 1st district · a winter afternoon, 1913',
        glb: 'cafe-central.glb',
        blurb: 'The chess player in the corner edits a Russian newspaper called Pravda from a flat across town. When a foreign-ministry official was warned that Russia might have a revolution, he is said to have asked who would lead it, "Herr Bronstein from the Café Central?"',
        room: { w: 14, d: 11, h: 5, floor: 'checker', wall: '#c9b48c', trim: '#6b4a2e', sky: '#e8d9bd', windows: [{ wall: 'back', at: -4 }, { wall: 'back', at: 0 }, { wall: 'back', at: 4 }] },
        camera: { pos: [5.4, 3.5, 7.0], look: [-0.3, 1.1, -0.3] },
        props: [
          { type: 'column', at: [-3, -2] }, { type: 'column', at: [3, -2] }, { type: 'column', at: [-3, 2.5] }, { type: 'column', at: [3, 2.5] },
          { type: 'chandelier', at: [0, 0] },
          { type: 'table', at: [-2, 0] }, { type: 'chair', at: [-2, 0.8], rot: 180 }, { type: 'chair', at: [-2, -0.8] }, { type: 'chessboard', at: [-2, 0] },
          { type: 'table', at: [1.6, 1.2] }, { type: 'chair', at: [1.6, 2.0], rot: 180 }, { type: 'chair', at: [2.4, 1.2], rot: 270 },
          { type: 'table', at: [3.5, -2.2] }, { type: 'chair', at: [4.3, -2.2], rot: 270 },
          { type: 'table', at: [-4.5, -3.0] }, { type: 'chair', at: [-4.5, -2.2], rot: 180 }, { type: 'chair', at: [-5.3, -3.0], rot: 90 },
          { type: 'table', at: [0.5, -3.2] }, { type: 'chair', at: [0.5, -2.4], rot: 180 },
          { type: 'lamp', at: [-5.8, 3.2] }, { type: 'lamp', at: [5.8, 3.2] },
        ],
        figures: [
          { id: 'trotsky', age: 33, coat: '#2e2e34', hair: '#1a1a1a', name: 'Leon Trotsky', at: [-2, 0.8], face: 0, pose: 'sit', coat: '#2e2e34', hair: '#2a2016', glasses: true, moustache: true, beard: '#2a2016',
            note: 'Thirty-three, seven years into exile in Vienna as Lev Bronstein. Plays chess here most afternoons and edits the Vienna Pravda in between. Will meet Stalin for the first time this winter and remember only a "glint of animosity".' },
          { id: 'altenberg', age: 54, beard: '#b8b0a0', name: 'Peter Altenberg', at: [3.5, -1.4], face: 180, pose: 'sit', coat: '#8a7a66', hair: 'none', bald: true, moustache: true, skin: '#e8c8a8',
            note: 'The house poet. Gives the café as his postal address and is here every day. Alban Berg is setting five of his postcard poems to music; they will be sung in this city in March and stop the concert.' },
          { id: 'adler', age: 43, hair: '#2a2016', name: 'Alfred Adler', at: [-4.5, -2.2], face: 0, pose: 'sit', coat: '#3a3f4a', vest: '#6a6a5a', moustache: true, glasses: true,
            note: 'Freud\'s former deputy. Walked out of the Vienna Psychoanalytic Society two years ago and now runs his own school of "individual psychology" from tables like this one, a twenty-minute walk from Berggasse.' },
          { id: 'waiter', age: 30, hair: '#2a2016', moustache: true, pose: 'hold', name: 'The Herr Ober', at: [0.5, 1.2], face: 200, coat: '#151515', vest: '#f4f0e6', held: 'paper',
            note: 'A coffee buys the table for the afternoon and every newspaper in the house. The café is why so much of this city\'s work was done in public.' },
        ],
        sources: 'Trotsky, My Life (1930); Timms, Karl Kraus: Apocalyptic Satirist; the Café Central anecdote is told of Count Berchtold\'s ministry and is unverifiable, which is why it is famous.',
      },
    },
    {
      id: 'berggasse', label: 'Berggasse 19', x: 255, y: 178, labelSide: 'left',
      scene: {
        title: 'Berggasse 19', subtitle: 'Freud\'s consulting room, 9th district · 1913',
        glb: 'berggasse.glb',
        blurb: 'The couch has been here since 1891 and will stay until 1938. This year Freud publishes Totem and Taboo and loses Jung, his chosen heir, in a break he treats as a bereavement.',
        room: { w: 9, d: 8, h: 4, floor: '#5a3a24', wall: '#7a5a3a', trim: '#3a2416', sky: '#d8c8b0', windows: [{ wall: 'left', at: -1 }] },
        camera: { pos: [4.2, 3.2, 5.6], look: [-0.6, 0.9, -0.8] },
        props: [
          { type: 'rug', at: [0, 0], w: 6, d: 5, color: '#7a2f2f' },
          { type: 'couch', at: [-0.6, -1.6], rot: 0 }, { type: 'armchair', at: [-2.6, -1.5], rot: 90 },
          { type: 'desk', at: [2.0, -2.8] }, { type: 'chair', at: [2.0, -2.0], rot: 180 },
          { type: 'bookshelf', at: [3.0, -3.6], w: 2.4 }, { type: 'cabinet', at: [-3.0, -3.6] }, { type: 'bookshelf', at: [4.2, 0], rot: 270, w: 3 },
          { type: 'lamp', at: [0.5, -2.2] },
        ],
        figures: [
          { id: 'freud', age: 56, model: 'male-b', name: 'Sigmund Freud', at: [-2.6, -1.5], face: 90, pose: 'lounge', coat: '#3a3a3a', vest: '#5a5a5a', hair: '#8a8a8a', beard: '#8a8a8a', glasses: true, skin: '#ddb090',
            note: 'Fifty-six. Sits behind the patient, out of sight, because he "cannot put up with being stared at for eight hours a day". Smokes twenty cigars a day and is about to write The Moses of Michelangelo.' },
          { id: 'patient', age: 30, sex: 'female', dress: '#6a5a7a', hairstyle: 'bob01', name: 'A patient', at: [-0.3, -1.4], face: 60, pose: 'lounge', coat: '#6a5a7a', hair: '#3a2a1a',
            note: 'Six sessions a week, an hour each, about a year. The couch is the only piece of furniture in this room a reader would recognise, and it was a gift from a grateful patient.' },
          { id: 'anna', age: 17, sex: 'female', dress: '#8a6a5a', hairstyle: 'braid01', name: 'Anna Freud', at: [2.0, -1.9], face: 180, pose: 'sit', coat: '#8a6a5a', hair: '#3a2a1a', held: 'paper',
            note: 'Seventeen, the youngest of six, about to become a schoolteacher. Will be analysed by her father, which even his followers thought was a bad idea, and will carry the whole enterprise to London in 1938.' },
        ],
        sources: 'Gay, Freud: A Life for Our Time; the Freud Museum, Vienna and London.',
      },
    },
    {
      id: 'musikverein', label: 'Musikverein', x: 512, y: 466,
      scene: {
        title: 'The Skandalkonzert', subtitle: 'Musikverein, Großer Saal · 31 March 1913, about 9 pm',
        glb: 'musikverein.glb',
        blurb: 'Schoenberg conducts his own music and his students\'. During Berg\'s Altenberg songs the audience starts a fight, the police are called, and the concert ends before the Mahler on the programme is reached.',
        room: { w: 16, d: 14, h: 6, floor: '#8a6a3a', wall: '#d9c07a', trim: '#a88a3a', sky: '#f0e4c4', windows: [] },
        camera: { pos: [5.5, 4.6, 9.5], look: [-0.5, 1.2, -1.5] },
        props: [
          { type: 'chandelier', at: [-4, 0] }, { type: 'chandelier', at: [4, 0] },
          { type: 'column', at: [-7.5, -6] }, { type: 'column', at: [7.5, -6] }, { type: 'column', at: [-7.5, 2] }, { type: 'column', at: [7.5, 2] },
          { type: 'podium', at: [0, -3.2], rot: 180 },
          { type: 'stand', at: [-2, -4.6], rot: 160 }, { type: 'stand', at: [-1, -5.2], rot: 170 }, { type: 'stand', at: [1, -5.2], rot: 190 }, { type: 'stand', at: [2, -4.6], rot: 200 },
          { type: 'stand', at: [-3.2, -5.6], rot: 150 }, { type: 'stand', at: [3.2, -5.6], rot: 210 }, { type: 'stand', at: [0, -6.0], rot: 180 },
          { type: 'chair', at: [-2, -4.2], rot: 340 }, { type: 'chair', at: [-1, -4.8], rot: 350 }, { type: 'chair', at: [1, -4.8], rot: 10 }, { type: 'chair', at: [2, -4.2], rot: 20 },
          { type: 'chair', at: [-3.2, -5.2], rot: 330 }, { type: 'chair', at: [3.2, -5.2], rot: 30 }, { type: 'chair', at: [0, -5.6], rot: 0 },
          { type: 'seats', at: [0, -0.5], rows: 5, cols: 12 },
        ],
        figures: [
          { id: 'schoenberg', age: 38, pose: 'hold', name: 'Arnold Schoenberg', at: [0, -3.2], face: 180, coat: '#1a1a1a', vest: '#f4f0e6', hair: 'none', bald: true, held: 'baton',
            note: 'Thirty-eight, conducting. Has stopped the orchestra to demand that the police remove anyone disturbing the peace. Will move his family out of Vienna within the year.' },
          { id: 'berg', age: 28, model: 'male-d', name: 'Alban Berg', at: [-1.0, 4.9], face: 10, coat: '#2a2a30', hair: '#2a2016',
            note: 'Twenty-eight. Two of his five Altenberg Lieder are being played for the first time. The fight starts during them. He will not hear them performed complete in his lifetime.' },
          { id: 'webern', age: 29, model: 'male-e', name: 'Anton Webern', at: [-4.6, 0.8], face: 60, pose: 'yes', coat: '#2a2a30', glasses: true, hair: '#4a3a2a',
            note: 'Twenty-nine. His Six Pieces for Orchestra opened the evening. Is reported to have stood up and shouted that the hecklers should be thrown out, which did not calm the hall.' },
          { id: 'buschbeck', age: 24, pose: 'akimbo', hair: '#2a2016', name: 'Erhard Buschbeck', at: [0, 3.6], face: 180, coat: '#3a3a44',
            note: 'The concert\'s organiser, twenty-four. Punches a heckler; the case goes to court. There, the operetta composer Oscar Straus testifies that the slap was the most harmonious sound of the evening.' },
          { id: 'heckler', age: 40, pose: 'akimbo', hair: '#2a2016', name: 'A heckler', at: [1.2, 3.8], face: 200, coat: '#5a4a3a', hat: 'bowler', moustache: true,
            note: 'One of many. Vienna\'s concert public treats new music as an invitation to a fight, and had the Mahler on the programme been reached it would probably have been the same.' },
        ],
        sources: 'Ross, The Rest Is Noise; contemporary reports in the Neue Freie Presse, 1 April 1913.',
      },
    },
    {
      id: 'hofburg', label: 'Hofburg', x: 400, y: 318, labelSide: 'left',
      scene: {
        title: 'The Emperor\'s study', subtitle: 'Hofburg, Leopoldine Wing · half past four in the morning, 1913',
        glb: 'hofburg.glb',
        blurb: 'Franz Joseph is eighty-two and has reigned since 1848. He gets up at four, works standing at a desk, and signs everything himself, a habit that has kept the empire running and prevented anyone else from learning how.',
        room: { w: 10, d: 9, h: 5, floor: '#7a5a3a', wall: '#e8dfc8', trim: '#c8a860', sky: '#d0c4b0', windows: [{ wall: 'left', at: -2 }, { wall: 'left', at: 1 }] },
        camera: { pos: [4.3, 3.0, 5.4], look: [-0.5, 1.2, -1] },
        props: [
          { type: 'rug', at: [0, 0], w: 7, d: 6, color: '#8a3a3a' },
          { type: 'standingdesk', at: [-1.5, -2.5], rot: 20 },
          { type: 'desk', at: [2.5, -2.8] }, { type: 'chair', at: [2.5, -2.0], rot: 180 },
          { type: 'cabinet', at: [-3.5, -3.8] }, { type: 'bookshelf', at: [1.5, -4.0], w: 3 },
          { type: 'chandelier', at: [0, 0] }, { type: 'armchair', at: [3.5, 1.5], rot: 250, color: '#8a2f2f' },
          { type: 'lamp', at: [-3.8, 1.8] },
        ],
        figures: [
          { id: 'franzjoseph', age: 82, pose: 'hold', bald: true, name: 'Franz Joseph I', at: [-1.5, -1.6], face: 200, coat: '#3a5a8a', vest: '#f4f0e6', hair: '#d8d8d8', bald: true, beard: '#d8d8d8', moustache: true, skin: '#e8c0a0', held: 'paper',
            note: 'Has outlived his brother (shot in Mexico), his son (Mayerling) and his wife (stabbed in Geneva). Sleeps on an iron camp bed. Believes the archduke who will succeed him is a danger to the monarchy, and is right about the timing if not the reason.' },
          { id: 'adjutant', age: 35, pose: 'attention', hair: '#2a2016', name: 'Adjutant on duty', at: [2.5, 1.0], face: 300, coat: '#2e4a2e', hat: 'military', moustache: true,
            note: 'The first of a stream of officials that will run until lunch. Audiences last as long as the emperor stays standing, which is the whole audience.' },
        ],
        sources: 'Unterreiner, Franz Joseph 1830–1916; the Kaiserappartements, Hofburg.',
      },
    },
    {
      id: 'belvedere', label: 'Belvedere', x: 760, y: 468,
      scene: {
        title: 'The heir\'s residence', subtitle: 'Lower Belvedere, 3rd district · spring 1913',
        glb: 'belvedere.glb',
        blurb: 'Franz Ferdinand runs a shadow government from here, with his own military chancellery, and waits for an uncle who will not die. Fifteen months from now he will drive through Sarajevo.',
        room: { w: 11, d: 9, h: 5, floor: '#6a4a2a', wall: '#dcd0b8', trim: '#8a6a48', sky: '#dfe4d8', windows: [{ wall: 'back', at: -3 }, { wall: 'back', at: 3 }] },
        camera: { pos: [5.5, 3.6, 7], look: [0, 1.2, -1] },
        props: [
          { type: 'rug', at: [0, 0], w: 7, d: 6, color: '#3a5a3a' },
          { type: 'desk', at: [0, -2.5] }, { type: 'chair', at: [0, -1.7], rot: 180 },
          { type: 'bookshelf', at: [-3.5, -3.8], w: 2.5 }, { type: 'bookshelf', at: [3.5, -3.8], w: 2.5 },
          { type: 'armchair', at: [-3.2, 0.8], rot: 90 }, { type: 'armchair', at: [3.0, 1.2], rot: 40 },
          { type: 'chandelier', at: [0, 0.5] },
          { type: 'cabinet', at: [-5.0, 1.5], rot: 90 },
        ],
        figures: [
          { id: 'franzferdinand', age: 49, model: 'male-f', name: 'Archduke Franz Ferdinand', at: [0, -1.7], face: 180, pose: 'sit', coat: '#2e4a2e', vest: '#c8a860', moustache: true, hair: '#4a3a2a', skin: '#e0b898',
            note: 'Forty-nine. Has shot, by his own count, about 275,000 animals. Wants to turn the dual monarchy into a triple one with a Slav crown, which is exactly why some Serbs want him dead.' },
          { id: 'sophie', age: 44, sex: 'female', dress: '#7a4a6a', hairstyle: 'long01', name: 'Sophie, Duchess of Hohenberg', at: [3.0, 1.2], face: 40, pose: 'lounge', coat: '#7a4a6a', hair: '#3a2a1a', shawl: '#c8b8d8',
            note: 'A countess, not an archduchess, which at this court means she cannot sit beside her husband at dinner or ride in his carriage in Vienna. In Sarajevo, as an army inspector\'s wife, she can. That is one reason they go.' },
          { id: 'brosch', age: 43, pose: 'attention', hair: '#2a2016', name: 'Major Brosch', at: [-2.4, -2.6], face: 120, coat: '#2e4a2e', hat: 'military', moustache: true, held: 'paper',
            note: 'Head of the military chancellery, which the archduke has built into a government-in-waiting with its own foreign policy. Every ambition in the empire files through this room in duplicate.' },
        ],
        sources: 'King & Woolmans, The Assassination of the Archduke.',
      },
    },
    {
      id: 'stalin', label: 'Stalin\'s lodgings', x: 40, y: 600, labelSide: 'right', offmap: { arrow: '↙', distance: '4 km' },
      scene: {
        title: 'Schönbrunner Schloßstraße 30', subtitle: 'The Troyanovskys\' flat, 12th district · February 1913',
        glb: 'stalin.glb',
        blurb: 'Stalin is in Vienna for five weeks, his only extended stay in the West, writing the pamphlet that will make him the Bolsheviks\' expert on nationalities. He does not read German, so a twenty-four-year-old named Bukharin reads it for him.',
        room: { w: 7, d: 6, h: 3.4, floor: '#6a5a4a', wall: '#b8b0a0', trim: '#5a4a3a', sky: '#c8c4bc', windows: [{ wall: 'back', at: 1.5 }] },
        camera: { pos: [4.4, 3.0, 5.4], look: [-0.3, 0.9, -0.6] },
        props: [
          { type: 'desk', at: [-1.6, -2.0] }, { type: 'chair', at: [-1.6, -1.2], rot: 180 },
          { type: 'bookshelf', at: [2.4, -2.5], w: 1.4 }, { type: 'chair', at: [1.0, -0.6], rot: 250 },
          { type: 'rug', at: [0, 0.4], w: 3.2, d: 2.6, color: '#5a4a5a' }, { type: 'lamp', at: [2.9, 1.6] },
          { type: 'bunk', at: [-2.6, 1.4], rot: 270 },
        ],
        figures: [
          { id: 'stalin', age: 34, model: 'male-f', name: 'Joseph Stalin', at: [-1.6, -1.2], face: 180, pose: 'sit', coat: '#3a3a3a', hair: '#1a1a1a', moustache: true, skin: '#d8a888',
            note: 'Thirty-four, travelling as Stavros Papadopoulos on a stolen passport. Signs this pamphlet "K. Stalin", the first time the name appears in print. Walks daily in the Schönbrunn park. Hitler walks there too; whether they passed each other is unknowable, which has not stopped anyone.' },
          { id: 'bukharin', age: 24, model: 'male-e', name: 'Nikolai Bukharin', at: [1.0, -0.6], face: 250, pose: 'sit', coat: '#4a4a5a', hair: '#8a5a2a', beard: '#8a5a2a', glasses: true,
            note: 'Studying at the university under Böhm-Bawerk, the empire\'s finance minister, and spending afternoons in the Hofbibliothek translating the Austro-Marxists for a man who will have him shot in 1938.' },
          { id: 'troyanovsky', age: 30, hair: '#2a2016', name: 'Alexander Troyanovsky', at: [0.3, 1.5], face: 150, coat: '#5a5a6a', vest: '#8a8a7a', moustache: true,
            note: 'The host, a Bolshevik of good family, whose flat is the Vienna post office for the Russian underground. Will end up Soviet ambassador in Washington.' },
        ],
        sources: 'Montefiore, Young Stalin; Trotsky, Stalin (1941).',
      },
    },
    {
      id: 'hitler', label: 'Hitler\'s hostel', x: 240, y: 30, labelSide: 'right', offmap: { arrow: '↑', distance: '3 km' },
      scene: {
        title: 'Männerheim Meldemannstraße', subtitle: 'The men\'s hostel, 20th district · spring 1913',
        glb: 'hitler.glb',
        blurb: 'Hitler has lived in this hostel for three years, painting postcard views of the city that other lodgers sell for him. In May he will turn twenty-four, collect his father\'s inheritance, and take the train to Munich, mostly to avoid being called up by the army he is about to lose.',
        room: { w: 14, d: 8, h: 4, floor: 'concrete', wall: '#c8c0b0', trim: '#7a7a7a', sky: '#d0ccc4', windows: [{ wall: 'back', at: -4 }, { wall: 'back', at: 0 }, { wall: 'back', at: 4 }] },
        camera: { pos: [4.8, 3.0, 5.6], look: [-0.5, 1, -0.5] },
        props: [
          { type: 'table', at: [-1.5, 0], r: 0.9, color: '#d8c8a8' }, { type: 'table', at: [2.5, 0], r: 0.9, color: '#d8c8a8' },
          { type: 'chair', at: [-1.5, 1.1], rot: 180 }, { type: 'chair', at: [-2.6, 0], rot: 90 }, { type: 'chair', at: [-0.4, 0], rot: 270 },
          { type: 'chair', at: [2.5, 1.1], rot: 180 }, { type: 'chair', at: [3.6, 0], rot: 270 },
          { type: 'easel', at: [-2.4, -1.4], rot: -35, paint: '#c8b088' },
          { type: 'bunk', at: [5.5, -2.5] }, { type: 'bunk', at: [-5.5, 2.5] }, { type: 'bunk', at: [5.5, 2.5] },
          { type: 'bookshelf', at: [1, -3.6], w: 2 },
        ],
        figures: [
          { id: 'hitler', age: 23, pose: 'interact', name: 'Adolf Hitler', at: [-3.4, -0.7], face: 55, coat: '#4a4a48', hair: '#2a2016', moustache: 'small', held: 'brush', skin: '#e8c8a8',
            note: 'Twenty-three. Paints the Karlskirche and the Parliament from other people\'s postcards, two a day, and lectures the reading room on Wagner and the Jews. Nobody here will remember him as anything but a crank.' },
          { id: 'neumann', age: 35, hair: '#2a2016', name: 'Josef Neumann', at: [-1.5, 1.1], face: 0, pose: 'sit', coat: '#5a5040', hat: 'cap', capColor: '#3a3a3a',
            note: 'A Jewish copper-polisher who sells the paintings and lends Hitler money. They get on well. Hitler will later say he saw no Jews as enemies until the war, which is untrue, but this is the man he meant.' },
          { id: 'lodger', age: 40, pose: 'sit', name: 'Another lodger', at: [3.6, 0], face: 270, coat: '#6a6058', hat: 'cap', capColor: '#5a4a3a', held: 'paper',
            note: 'Five hundred beds, a reading room, a kitchen, and a bath, for a schilling a week. The best men\'s hostel in Europe, built by a Jewish foundation, and the last address Hitler will have before Munich.' },
        ],
        sources: 'Hamann, Hitler\'s Vienna; Kershaw, Hitler 1889–1936: Hubris.',
      },
    },
    {
      id: 'tito', label: 'Tito, Wiener Neustadt', x: 560, y: 615, labelSide: 'right', offmap: { arrow: '↓', distance: '50 km' },
      scene: {
        title: 'The Daimler works', subtitle: 'Wiener Neustadt, 50 km south · 1913',
        glb: 'tito.glb',
        blurb: 'Josip Broz, twenty, is a mechanic and test driver at the Austro-Daimler factory, the best job he has ever had. In the autumn he is conscripted into the Austro-Hungarian army and sent east. He will come back with a different name and a country.',
        room: { w: 14, d: 10, h: 6, floor: 'concrete', wall: '#a8a49c', trim: '#6a6a6a', sky: '#cfd4d8', windows: [{ wall: 'back', at: -4.5 }, { wall: 'back', at: -1.5 }, { wall: 'back', at: 1.5 }, { wall: 'back', at: 4.5 }] },
        camera: { pos: [7, 4, 8], look: [0, 1, 0] },
        props: [
          { type: 'car', at: [0.8, 0.4], rot: 20 }, { type: 'car', at: [5.2, -2.6], rot: 90, color: '#6a2f2f' },
          { type: 'workbench', at: [-4.5, -3.8] }, { type: 'workbench', at: [-1.5, -4.0] },
          { type: 'column', at: [-6, -4] }, { type: 'column', at: [6, -4] },
          { type: 'lamp', at: [-5.5, 2.5] },
        ],
        figures: [
          { id: 'tito', age: 20, hair: '#2a2016', pose: 'both', name: 'Josip Broz', at: [-1.6, 1.8], face: 40, coat: '#3a4a6a', trousers: '#2a2a2a', hat: 'cap', capColor: '#2a2a2a', moustache: 'small',
            note: 'Fences and has learned to drive, which almost nobody his age can do. Will call the Daimler the place he "first felt like a skilled man". Thirty-two years from now he is Marshal Tito.' },
          { id: 'foreman', age: 45, hair: '#2a2016', pose: 'hold', name: 'The foreman', at: [-4.5, -2.9], face: 150, coat: '#4a4a4a', vest: '#7a7a6a', moustache: true, held: 'paper',
            note: 'Ferdinand Porsche runs this factory. It is not known that he ever spoke to the boy from Kumrovec, but he ran a tight shop, and the boy was one of the best mechanics in it.' },
        ],
        sources: 'West, Tito and the Rise and Fall of Yugoslavia; Dedijer, Tito Speaks.',
      },
    },
  ],
};
