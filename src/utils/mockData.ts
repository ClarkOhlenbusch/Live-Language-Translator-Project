import { TranscriptData } from '../types';

export const mockTranscriptData: TranscriptData[] = [
  {
    id: '1',
    italian: 'Ciao, come stai? Spero che oggi sia una bellissima giornata.',
    english: 'Hi, how are you? I hope today is a beautiful day.',
    replies: [
      { 
        italian: 'Sto molto bene, grazie! Anche io spero che tu abbia una giornata fantastica.',
        english: "I'm very well, thank you! I also hope you have a fantastic day."
      },
      {
        italian: 'Tutto bene, grazie. Anche per te!',
        english: 'All good, thanks. Same to you!'
      }
    ]
  },
  {
    id: '2',
    italian: 'Ieri ho studiato l\'italiano per tre ore. È una lingua bellissima ma difficile.',
    english: 'Yesterday I studied Italian for three hours. It\'s a beautiful but difficult language.',
    replies: [
      {
        italian: 'Complimenti per il tuo impegno! Stai facendo progressi?',
        english: 'Congratulations on your commitment! Are you making progress?'
      },
      {
        italian: 'Sì, l\'italiano richiede pratica costante. Continua così!',
        english: 'Yes, Italian requires constant practice. Keep it up!'
      }
    ]
  },
  {
    id: '3',
    italian: 'Mi piacerebbe visitare Roma quest\'estate. Hai qualche consiglio?',
    english: 'I would like to visit Rome this summer. Do you have any advice?',
    replies: [
      {
        italian: 'Roma è stupenda! Ti consiglio di visitare il Colosseo e i Musei Vaticani.',
        english: 'Rome is stunning! I recommend visiting the Colosseum and the Vatican Museums.'
      },
      {
        italian: 'Assolutamente! Evita agosto perché fa troppo caldo e la città è piena di turisti.',
        english: 'Absolutely! Avoid August because it\'s too hot and the city is full of tourists.'
      }
    ]
  }
];