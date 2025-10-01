import { usePreferencesStore } from "../../state/usePreferencesStore";

export default function NounSubMenu() {
  const nounOptions = usePreferencesStore((state) => state.nounOptions);
  const toggleNounOption = usePreferencesStore((state) => state.toggleNounOption);

  const options = ["identify: case", "identify: number", "identify: gender", "produce:case", "produce: number", "produce: gender"];
  const action_options = ["identify", "produce"]
  const subject_options = ["gender", "number", "case"]

  return (
    <div className="space-y-2">
      {options.map((option) => (
        <label key={option} className="block">
          <input
            type="checkbox"
            checked={nounOptions.includes(option)}
            onChange={() => toggleNounOption(option)}
            className="mr-2"
          />
          {option}
        </label>
      ))}
    </div>
  );
}