import Form from "next/form";
import InputClient from "@/app/files/componetns/InputClient";


function SearchForm() {
    return (
        <Form action="/files">
            <InputClient />
        </Form>
    );
}

export default SearchForm;