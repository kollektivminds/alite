import React from 'react';

function WordListSelector() {
  return (
    <div className="flex space-x-4 mb-6">
      <select className="border p-2 rounded w-64">
        <option>Choose pre-made list</option>
        <option>List A</option>
        <option>List B</option>
      </select>
      <input type="text" placeholder="Add a word..." className="border p-2 rounded w-64" />
    </div>
  );
}

export default WordListSelector;