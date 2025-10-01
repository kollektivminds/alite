export default function WordSelector() {
    const { addWordList, addCustomWord } = usePreferencesStore();
  
    return (
      <div className="flex space-x-4 mb-6">
        <select onChange={(e) => addWordList(e.target.value)} className="border p-2 rounded-lg">
          <option value="">Select Word List</option>
          <option value="chapter14">Chapter 14</option>
          <option value="verbs_of_motion">Verbs of Motion</option>
        </select>
  
        <input
          type="text"
          placeholder="Add a custom word"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              addCustomWord(e.target.value);
              e.target.value = "";
            }
          }}
          className="border p-2 rounded-lg"
        />
      </div>
    );
  }  