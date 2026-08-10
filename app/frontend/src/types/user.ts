
export type UserRole = 'student' | 'instructor';
export type AppTheme = 'light' | 'dark' | 'system';
export type TextSize = 'sm' | 'md' | 'lg';

/**
 * User Settings saved in DB and managed via React Context.
 */
export interface UserSettings {
  theme: AppTheme;
  textSize: TextSize;
  displayLanguage: 'en' | 'ru'; // i18n locale selection
  animationsEnabled: boolean;
}

export interface UserProfile {
  id: number;
  email: string;
  fullName: string;
  role: UserRole;
  settings: UserSettings;
}