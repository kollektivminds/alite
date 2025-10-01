import { useState } from "react";
import i18n from '../../i18n';
import { useTranslation } from 'react-i18next';

export default function Header() {
    const { t } = useTranslation();
    return (
        <div className="flex flex-col">
            <div className="flex"></div>
            <div className="flex"></div>
        </div>
    );
}