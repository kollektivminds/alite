import { grammarOptions } from '../config/grammarOptions'
import './GrammarMenu.css';

// --- Helper function to initialize the state ---
// Creates a flat object with all options set to 'false' initially.
const initializeSelections = () => {
  const initialState = {};
  grammarOptions.forEach(category => {
    category.options.forEach(option => {
      initialState[option.id] = false;
    });
  });
  return initialState;
};


function GrammarMenu() {
  const [selections, setSelections] = useState(initializeSelections);

  // --- Handle checkbox clicks ---
  const handleCheckboxChange = (event) => {
    const { name, checked } = event.target;
    setSelections(prevSelections => ({
      ...prevSelections,
      [name]: checked,
    }));
  };

  // --- Handle form submission ---
  const handleSubmit = () => {
    console.log("Current Selections:", selections);
    // This is where you would make an API call to your backend
    // to save the user's preferences and/or fetch exercises.
    // For example:
    // fetch('http://localhost:8000/api/save-preferences', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(selections),
    // });
    alert("Preferences submitted! Check the console.");
  };

  return (
    <div className="grammar-menu-container">
      <h3>Choose What to Study</h3>
      <div className="grammar-categories">
        {grammarOptions.map(category => (
          <div key={category.id} className="category-section">
            <h4>{category.displayName}</h4>
            <ul className="options-list">
              {category.options.map(option => (
                <li key={option.id}>
                  <label>
                    <input
                      type="checkbox"
                      name={option.id}
                      checked={selections[option.id]}
                      onChange={handleCheckboxChange}
                    />
                    {option.displayName}
                  </label>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <button onClick={handleSubmit} className="submit-button">
        Start Studying
      </button>
    </div>
  );
}

export default GrammarMenu;