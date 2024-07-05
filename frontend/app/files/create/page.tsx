// "use client";

// import React, { ChangeEvent, useEffect, useState } from "react";
// import { Select, SelectItem } from "@nextui-org/select";
// import { Input } from "@nextui-org/input";
// import { Button } from "@nextui-org/button";

// import { TagResponse } from "../../../types/interface/tags.interface";
// import { getTokenStorage } from "../../../services/auth/auth.helper";
// import { TagsService } from "../../../services/tags/tags.service";
// import { toastError } from "../../../utils/toast-error";
// import { FilesCreateRequestDTO } from "../../../types/interface/files.interface";
// import { FilesService } from "../../../services/files/files.service";
// import { toastSuccess } from "../../../utils/toast-success";
// import { fileTypes } from "../../../types/types/fileTypes";

// export default function FilesCreate() {
//   // const [name, setName] = useState("");
//   const [fileType, setFileType] = useState<string>("1");
//   const [tags, setTags] = useState<TagResponse[]>([]);
//   const [file, setFile] = useState<string | null>(null);
//   const [error, setError] = useState<string | null>(null);
//   const [nameTags, setNameTags] = useState("");
//   const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);
//   const token = getTokenStorage();

//   useEffect(() => {
//     fetchTags();
//   }, []);

//   const fetchTags = async () => {
//     try {
//       const res = await TagsService.gatAll();

//       setTags(res.results);
//     } catch (error) {
//       toastError(error);
//     }
//   };

//   const getFileMimeType = (fileName: string) => {
//     const extension = fileName.split(".").pop();

//     switch (extension) {
//       case "mp3":
//         return "mp3";
//       case "wav":
//         return "wav";
//       case "png":
//         return "png";
//       case "jpg":
//       case "jpeg":
//         return "jpeg";
//       case "gif":
//         return "gif";
//       case "pdf":
//         return "application/pdf";
//       default:
//         return "application/octet-stream";
//     }
//   };
//   const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
//     const selectedFile = e.target.files?.[0];

//     if (selectedFile) {
//       const reader = new FileReader();

//       reader.onloadend = () => {
//         const base64Data = reader.result as string;
//         const mimeType = getFileMimeType(selectedFile.name);

//         const base64String = `data:${selectedFile.name}/${mimeType};base64,${base64Data.split(",")[1]}`;

//         setFile(base64String);
//       };
//       reader.readAsDataURL(selectedFile);
//     } else {
//       setFile(null);
//     }
//   };

//   const handleCreateFile = async () => {
//     if (!file) {
//       setError("Пожалуйста, выберите файл");

//       return;
//     }

//     try {
//       const fileData: FilesCreateRequestDTO = {
//         // name,
//         file_type: Number(fileType),
//         source: file,
//         tags: selectedTagIds,
//       };

//       // const response = await FilesService.createFiles(fileData, token);

//       toastSuccess("File created successfully");
//       setSelectedTagIds([]);
//       setFile(null);
//       setError(null);
//     } catch (error) {
//       toastError(error);
//     }
//   };

//   const handleTagChange = (event: ChangeEvent<HTMLSelectElement>) => {
//     const selectedKeys = new Set(
//       Array.from(event.target.selectedOptions, (option) => option.value),
//     );

//     setSelectedTagIds(Array.from(selectedKeys).map(Number));
//   };

//   const handleTypeChange = (type: string) => {
//     setFileType(type);
//   };

//   const handleCreateTags = async () => {
//     const tagsData = { name: nameTags };

//     console.log(tagsData);

//     try {
//       const response = await FilesService.createTags(tagsData, token);

//       console.log("Tags created successfully:", response);
//       setNameTags("");
//       setError(null);
//     } catch (error: any) {
//       console.error("Error creating tags:", error);
//       setError(error.message);
//     }
//   };

//   return (
//     <div>
//       <form
//         className="flex gap-4 flex-col"
//         onSubmit={(e) => {
//           e.preventDefault();
//           handleCreateFile();
//         }}
//       >
//         <div>
//           <Select
//             defaultSelectedKeys={[`${fileType}`]}
//             label="Выберите тип файла"
//             onChange={(e) => handleTypeChange(e.target.value)}
//           >
//             {fileTypes.map((option) => (
//               <SelectItem key={option.key} value={option.key}>
//                 {option.label}
//               </SelectItem>
//             ))}
//           </Select>
//         </div>
//         <div>
//           <Select
//             multiple
//             label="Выберите тэги"
//             selectedKeys={new Set(selectedTagIds.map(String))}
//             onChange={handleTagChange}
//           >
//             {tags.map((option) => (
//               <SelectItem key={option.id} value={String(option.id)}>
//                 {option.name}
//               </SelectItem>
//             ))}
//           </Select>
//         </div>
//         <div>
//           {/* <Button style={{ width: "100%" }}> */}
//           <Input
//             // className={styles.file}
//             label="Выберите файл"
//             placeholder="Выберите файл"
//             type="file"
//             onChange={handleFileChange}
//           />
//           {/* </Button> */}
//         </div>
//         <Button color="secondary" type="submit">
//           Создать файл
//         </Button>
//       </form>
//       <form
//         className="flex gap-4 flex-col"
//         onSubmit={(e) => {
//           e.preventDefault();
//           handleCreateTags();
//         }}
//       >
//         <div>
//           <Input
//             label="Тег"
//             placeholder="Введите название тега"
//             type="text"
//             value={nameTags}
//             onChange={(e) => setNameTags(e.target.value)}
//           />
//           <Button color="secondary" type="submit">
//             Создать тег
//           </Button>
//         </div>
//       </form>
//       {/* <CustomModal
//         content={responseContent}
//         isOpen={modalIsOpen}
//         onRequestClose={closeModal}
//       /> */}
//       {error && <p style={{ color: "red" }}>{error}</p>}
//     </div>
//   );
// }

"use client";

export default function FilesCreate() {
  return <div>что-то заеб</div>;
}
