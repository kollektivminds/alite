import { usePreferencesStore } from "../../state/usePreferencesStore";

export default function VerbSubMenu() {
  const verbOptions = usePreferencesStore((state) => state.verbOptions);
  const toggleVerbOption = usePreferencesStore((state) => state.toggleVerbOption);
  console.log("Verb options state:", verbOptions);

  const options = [
    "identify: aspect",
    "identify: conjugation type",
    "conjugate by: type I",
    "conjugate by: type II",
    "conjugate by: full table",
    "conjugate by: past tense",
    "conjugate by: present-future tense",
  ];

  return (
    <div className="mt-4 space-y-2">
      {options.map((option) => (
        <label key={option} className="block">
          <input
            type="checkbox"
            checked={verbOptions.includes(option)}
            onChange={() => toggleVerbOption(option)}
            className="mr-2"
          />
          {option}
        </label>
      ))}
    </div>
  );
}
