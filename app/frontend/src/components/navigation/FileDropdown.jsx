import React, { useEffect, useState } from 'react';
import axios from 'axios';

function FileDropdown() {
  const [files, setFiles] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:8000/files')
      .then(response => {
        setFiles(response.data);
      })
      .catch(error => {
        console.error("Error fetching files:", error);
      });
  }, []);

  return (
    <select className="border p-2 rounded">
      {files.map((file, index) => (
        <option key={index} value={file}>
          {file}
        </option>
      ))}
    </select>
  );
}

export default FileDropdown;
