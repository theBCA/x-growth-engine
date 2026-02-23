# X Bot - Multilingual Support (English & Turkish)

## Overview

Your X bot can now support both English and Turkish! This guide shows you how to configure and use the bot in either language.

---

## 🌍 Language Configuration

### Setup in .env

```env
# Language setting (en or tr)
BOT_LANGUAGE=en

# Or for Turkish
BOT_LANGUAGE=tr

# Niche (can be in either language)
BOT_NICHE=technology
BOT_NICHE_TR=teknoloji

# Target audience (either language)
BOT_TARGET_AUDIENCE=developers
BOT_TARGET_AUDIENCE_TR=yazılımcılar
```

---

## 💻 Language System Implementation

### Create `src/utils/i18n.ts`

```typescript
import dotenv from 'dotenv';

dotenv.config();

type Language = 'en' | 'tr';

interface LanguageStrings {
  [key: string]: string;
}

interface Translations {
  en: LanguageStrings;
  tr: LanguageStrings;
}

// All translation strings
const translations: Translations = {
  en: {
    // Bot Messages
    'bot.starting': '🚀 Starting X Bot...',
    'bot.authenticated': '✓ Authenticated successfully',
    'bot.running': '✓ X Bot is running!',
    'bot.stopped': '🛑 Bot stopped',
    
    // Operations
    'op.like': 'Liking tweet from',
    'op.retweet': 'Retweeting from',
    'op.follow': 'Following user',
    'op.post': 'Posting content',
    'op.dm_sent': 'DM sent to',
    
    // Database
    'db.connecting': '📊 Connecting to database...',
    'db.connected': '✓ Connected to database',
    
    // Trends
    'trends.fetching': '🔍 Fetching trends...',
    'trends.found': 'Found {count} trends',
    
    // Errors
    'error.auth_failed': 'Authentication failed',
    'error.rate_limited': 'Rate limited, waiting 15 minutes...',
    'error.tweet_not_found': 'Tweet not found',
    'error.user_not_found': 'User not found',
    
    // Success
    'success.liked': 'Successfully liked',
    'success.retweeted': 'Successfully retweeted',
    'success.followed': 'Successfully followed',
    
    // Warnings
    'warn.approaching_limit': 'Approaching rate limit',
    'warn.account_restricted': 'Account may be restricted',
  },
  
  tr: {
    // Bot Messages
    'bot.starting': '🚀 X Bot başlatılıyor...',
    'bot.authenticated': '✓ Başarıyla doğrulandı',
    'bot.running': '✓ X Bot çalışıyor!',
    'bot.stopped': '🛑 Bot durduruldu',
    
    // Operations
    'op.like': 'Tweet beğeniliyor',
    'op.retweet': 'Retweet yapılıyor',
    'op.follow': 'Kullanıcı takip ediliyor',
    'op.post': 'İçerik yayınlanıyor',
    'op.dm_sent': 'DM gönderildi',
    
    // Database
    'db.connecting': '📊 Veritabanına bağlanılıyor...',
    'db.connected': '✓ Veritabanına bağlandı',
    
    // Trends
    'trends.fetching': '🔍 Trendler getiriliyor...',
    'trends.found': '{count} trend bulundu',
    
    // Errors
    'error.auth_failed': 'Kimlik doğrulama başarısız',
    'error.rate_limited': 'Hız sınırı, 15 dakika bekleniyor...',
    'error.tweet_not_found': 'Tweet bulunamadı',
    'error.user_not_found': 'Kullanıcı bulunamadı',
    
    // Success
    'success.liked': 'Başarıyla beğenildi',
    'success.retweeted': 'Başarıyla retweet edildi',
    'success.followed': 'Başarıyla takip edildi',
    
    // Warnings
    'warn.approaching_limit': 'Hız sınırına yaklaşılıyor',
    'warn.account_restricted': 'Hesap kısıtlı olabilir',
  }
};

class I18n {
  private language: Language;

  constructor(lang?: Language) {
    this.language = (lang || (process.env.BOT_LANGUAGE as Language) || 'en') as Language;
    
    if (!['en', 'tr'].includes(this.language)) {
      console.warn(`Language ${this.language} not supported, defaulting to English`);
      this.language = 'en';
    }
  }

  /**
   * Get translated string
   */
  t(key: string, replacements?: { [key: string]: string | number }): string {
    let text = translations[this.language][key] || translations['en'][key] || key;
    
    // Replace placeholders
    if (replacements) {
      Object.entries(replacements).forEach(([key, value]) => {
        text = text.replace(`{${key}}`, String(value));
      });
    }
    
    return text;
  }

  /**
   * Set language
   */
  setLanguage(lang: Language): void {
    if (['en', 'tr'].includes(lang)) {
      this.language = lang;
    }
  }

  /**
   * Get current language
   */
  getLanguage(): Language {
    return this.language;
  }
}

export default new I18n();
```

### Usage in Your Code

```typescript
import i18n from './utils/i18n';

// In your bot initialization
console.log(i18n.t('bot.starting'));
console.log(i18n.t('bot.authenticated'));

// With replacements
console.log(i18n.t('trends.found', { count: 10 }));

// In logging
await ActivityQueries.log(
  'like_tweet',
  tweetId,
  'success',
  i18n.t('success.liked')
);
```

---

## 🤖 Turkish AI Prompts

### 1. Tweet Reply Generation (Turkish)
```
SİSTEM PROMPTU:
Yardımcı, ilişkili ve samimi bir Twitter kullanıcısı olarak yanıt verin. 
Konuşmalara değer katan anlamlı yanıtlar yazınız. Asla spam, promosyon 
veya sahte olmayın. Kısa tutun, ilgili emojileri kullanın ve samimi şekilde katılın.

KULLANICI PROMPTU:
Bu tweete ilişkili yanıt yazın:
"[ORİJİNAL_TWEET]"

280 karakterin altında tutun. Yanıt:
- İlgili ve değer katmalı
- Samimi ilgi göstermelidır
- Konuşma tarzında olmalı, satış amaçlı değil
- 1-2 uygun emoji içerebilir
- Tartışmayı teşvik etmelidır

Yanıt:
```

### 2. Original Tweet Based on Trends (Turkish)
```
SİSTEM PROMPTU:
Twitter uzmanı olarak orijinal içerik oluşturun. Tweet yazın:
- Özgün ve değer katıcı
- Hedef kitlenizle rezonans yapan
- Net bir bakış açısı
- İlgili hashtag'ler (2-3 maksimum)
- Uygun olduğunda çağrı-harekete

KULLANICI PROMPTU:
Trending konusu hakkında orijinal tweet yazın: "[KONU]"

Hedef kitle: [KİTLE]
Uzmanlık alanınız: [NİŞ]

Tweet olmalı:
- 280 karakterin altında (veya thread formatı)
- İlişkili ve konuşmaya açık
- Marka sesinize özgü
- Trend verilerine dayalı

Tweet:
```

### 3. DM Response (Turkish)
```
SİSTEM PROMPTU:
Özel mesajlarda samimi ve yardımcı olun. Yanıtlar:
- Kişisel ve özgün
- Kısa (uzun yazılar yazma)
- Aksiyon odaklı gerekirse
- Daha ileri konuşmaya açık

KULLANICI PROMPTU:
Bu DM'e yanıt oluştur:
"[DM_MESAJI]"

Kullanıcı: @[KULLANICI_ADI]

Yanıt olmalı:
- 1-3 cümle maksimum
- Sorusunu doğrudan yanıtla
- Değer veya sonraki adımları sun
- Doğal şekilde konuşmayı devam ettir

Yanıt:
```

---

## 🔄 Switching Languages

### Runtime Language Switch

```typescript
// Change language at runtime
i18n.setLanguage('tr');  // Switch to Turkish
i18n.setLanguage('en');  // Switch to English

// Get current language
const currentLang = i18n.getLanguage();
console.log(`Current language: ${currentLang}`);
```

### Per-Account Language

If running multiple bots:

```env
# Bot 1 (English)
BOT_1_LANGUAGE=en
BOT_1_ACCOUNT_ID=123456

# Bot 2 (Turkish)
BOT_2_LANGUAGE=tr
BOT_2_ACCOUNT_ID=789012
```

---

## 📝 Adding More Languages

### To add a new language:

1. **Update Language Type**
```typescript
type Language = 'en' | 'tr' | 'de'; // Add new language
```

2. **Add Translations**
```typescript
const translations: Translations = {
  en: { /* ... */ },
  tr: { /* ... */ },
  de: { // Add new language
    'bot.starting': '🚀 X-Bot wird gestartet...',
    'bot.authenticated': '✓ Erfolgreich authentifiziert',
    // ... add all translations
  }
};
```

3. **Update .env**
```env
BOT_LANGUAGE=de
```

---

## 🎯 Turkish Bot Operations

### Turkish Daily Routine

```
06:00 Sabah Rutin
├─ Trend'leri getir
├─ Tweet'leri ara
└─ Puanlandır

09:00 Beğenme Fazı
├─ 50-100 tweet beğen
├─ 30-60 saniye bekle
└─ Kaydet

12:00 Retweet Fazı
├─ 20-30 tweet retweet et
├─ 5-10 dakika bekle
└─ Kaydet

18:00 Takip Fazı
├─ 50-100 kullanıcı takip et
├─ 2-5 dakika bekle
└─ DM'leri kontrol et

22:00 Gece Rutini
├─ İçerik oluştur
├─ Tweet at
└─ Yarın hazırla
```

---

## 🌐 Turkish Hashtag Strategy

### Popular Turkish Hashtags to Target

```
#TürkçeTwitter
#TechTürkiye
#Yazılımcılar
#StartupTR
#GirişimcilikTürkiye
#BloggerTR
#DigitalMarketingTR
#SosyalMedyaTR
#WebGeliştirme
#MobilUygulamalar
```

---

## 📊 Turkish Growth Metrics

### Expected Results (Turkish Market)

- **Follower Growth**: 50-150/ay (daha az rekabet)
- **Engagement Rate**: 2-5% (daha yüksek)
- **Follow-back Rate**: 25-40%
- **Best Times**: 20:00-23:00 (Türkiye saati)

---

## 💡 Tips for Turkish Bot Success

### Best Practices

✅ Use proper Turkish spelling and grammar
✅ Reference Turkish events and dates
✅ Engage with Turkish tech community
✅ Post during Turkish business hours (09:00-23:00)
✅ Use Turkish emojis and expressions
✅ Follow Turkish influencers in your niche
✅ Participate in Turkish Twitter trends
✅ Use Turkish hashtags strategically

### Avoid

✗ Machine translations (look natural)
✗ Mixing English and Turkish too much
✗ Posting during late night (Turkish time)
✗ Non-Turkish content that doesn't resonate
✗ Ignoring Turkish cultural nuances

---

## 📋 Multilingual Checklist

- [ ] Create `src/utils/i18n.ts`
- [ ] Add language to .env
- [ ] Update main.ts to use i18n
- [ ] Update all console.log statements
- [ ] Translate all prompts
- [ ] Test English mode
- [ ] Test Turkish mode
- [ ] Verify all messages display correctly
- [ ] Document language-specific timing
- [ ] Test language switching

---

## 🎯 Example: Complete Turkish Setup

### .env
```env
BOT_LANGUAGE=tr
BOT_NICHE=teknoloji
BOT_TARGET_AUDIENCE=yazılımcılar
BOT_ACCOUNT_ID=your_user_id
X_CLIENT_ID=your_id
X_CLIENT_SECRET=your_secret
```

### Initial Log (Turkish)
```
🚀 X Bot başlatılıyor...
📊 Veritabanına bağlanılıyor...
✓ Veritabanına bağlandı
✓ Başarıyla doğrulandı
✓ X Bot çalışıyor! (Dil: TR)
```

---

## Summary

Your X bot now supports:
✅ Full English support
✅ Full Turkish support
✅ Easy language switching
✅ Culturally appropriate content
✅ Turkish-specific strategies
✅ Easy to add more languages

The bot will work perfectly with Turkish content, Turkish hashtags, and Turkish audience while maintaining full functionality for English users.

**Ready to go multilingual! 🌍**
