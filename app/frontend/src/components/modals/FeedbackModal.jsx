import React, { useState } from 'react';
import { usePreferencesStore } from '../../state/usePreferencesStore';
import '../../css/FeedbackModal.css';
import { useTranslation } from 'react-i18next';


export default function FeedbackModal({ onClose }) {
  const [category, setCategory] = useState('bug'); // 'bug' | 'feature' | 'general'
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { t, i18n } = useTranslation();

  // Grab preferences to send with the feedback
  // const { difficulty, theme } = usePreferencesStore.getState();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message) {
      alert('Please enter a message.');
      return;
    }
    setIsSubmitting(true);

    // --- Prepare the data payload ---
    const feedbackData = {
      category,
      message,
      email: email || null, // Send null if empty
      // Automated context
      context: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        preferences: {
          difficulty,
          theme,
        },
      },
      submittedAt: new Date().toISOString(),
    };

    console.log('Submitting feedback:', feedbackData);

    // TODO: Send this data to your backend API
    // await fetch('/api/feedback', { method: 'POST', body: JSON.stringify(feedbackData) });
    
    // Simulate network request
    await new Promise(res => setTimeout(res, 1000));
    
    setIsSubmitting(false);
    alert('Thank you for your feedback!');
    onClose();
  };

  return (
    // <div className="modal-backdrop">
      <div className="modal-content flex-grow p-6 overflow-y-auto">
        <h2>{t('modalFeedback.submit')} {t('modalFeedback.feedback', { postProcess: 'lowercase' })}</h2>
        <form onSubmit={handleSubmit}>
          <label htmlFor="category-select">{t('modalFeedback.category')}</label>
          <select className='max-h-fit' id="category-select" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="bug">{t('modalFeedback.bug_report')}</option>
            <option value="feature">{t('modalFeedback.feature_request')}</option>
            <option value="general">{t('modalFeedback.general_feedback')}</option>
          </select>

          <label htmlFor="message-textarea">{t('modalFeedback.message')}</label>
          <textarea
            id="message-textarea"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={t('modalFeedback.message_placeholder')}
            required
          />

          <label htmlFor="email-input">{t('modalFeedback.email')}</label>
          <input
            id="email-input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t('modalFeedback.email_placeholder')}
          />

          <p className="context-disclaimer">
          {t('modalFeedback.tech_disclaimer')}
          </p>

          <div className='flex-shrink-0 p-6 border-t flex justify-end gap-4'>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? t('modalFeedback.submitting') : t('modalFeedback.submit')}
            </button>
            <button type="button" onClick={onClose} disabled={isSubmitting}>
            {t('modalFeedback.cancel')}
            </button>
          </div>
        </form>
      </div>
    // </div>
  );
}