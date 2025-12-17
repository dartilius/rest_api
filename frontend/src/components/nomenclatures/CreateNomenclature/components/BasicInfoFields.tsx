import {ICreateNomenclature} from "@/types/nomeclaturesType";
import {ChangeEvent} from "react";
import {TextField, Typography} from "@mui/material";

export const BasicInfoFields = ({
	formState,
	handleTextChange,
}: {
	formState: ICreateNomenclature
	handleTextChange: (
		field: keyof Omit<ICreateNomenclature, 'settings'>,
	) => (e: ChangeEvent<HTMLInputElement>) => void
}) => (
	<>
		<TextField
			label='Название'
			type='text'
			fullWidth
			margin='dense'
			value={formState.name}
			onChange={handleTextChange('name')}
			inputProps={{ maxLength: 250 }}
		/>
		<Typography
			variant='caption'
			sx={{ display: 'block', textAlign: 'right', mt: -1 }}
		>
			{formState.name.length}/250
		</Typography>

		<TextField
			label='Описание'
			type='text'
			fullWidth
			margin='dense'
			value={formState.description}
			onChange={handleTextChange('description')}
			inputProps={{ maxLength: 250 }}
		/>
		<Typography
			variant='caption'
			sx={{ display: 'block', textAlign: 'right', mt: -1 }}
		>
			{formState.description.length}/250
		</Typography>
	</>
)