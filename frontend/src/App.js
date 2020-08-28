import React, {useState} from 'react';
import './App.css';
import Button from '@material-ui/core/Button';
import axios from 'axios';
import Select from "@material-ui/core/Select";
import TextField from "@material-ui/core/TextField";
import Dialog from "@material-ui/core/Dialog";
import DialogTitle from "@material-ui/core/DialogTitle";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogActions from "@material-ui/core/DialogActions";
import Chip from "@material-ui/core/Chip";
import FormControl from "@material-ui/core/FormControl";
import InputLabel from "@material-ui/core/InputLabel";

function App() {
  const [entities, setEntities] = useState([]);
  const [emailAddress, setEmailAddress] = useState('');
  const [opType, setOpType] = useState('total_count');
  const [openDialog, setOpenDialog] = useState(null);
  const [emailError, setEmailError] = useState(null);
  const [entitiesError, setEntitiesError] = useState(null);

  const emailAddressIsValid = () => {
      let pattern = new RegExp(/^(("[\w-\s]+")|([\w-]+(?:\.[\w-]+)*)|("[\w-\s]+")([\w-]+(?:\.[\w-]+)*))(@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$)|(@\[?((25[0-5]\.|2[0-4][0-9]\.|1[0-9]{2}\.|[0-9]{1,2}\.))((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[0-9]{1,2})\.){2}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[0-9]{1,2})\]?$)/i);
      if (emailAddress !== '' && pattern.test(emailAddress)) {
          setEmailError(null);
          return true;
      } else {
          setEmailError("Please provide a valid email address");
          return false;
      }
  }

  const entitiesListIsValid = () => {
      if (entities.length > 0) {
          setEntitiesError(null);
          return true;
      } else {
          setEntitiesError("Please provide a list of entities");
          return false;
      }
  }

  const inputIsValid = () => {
      let emailValid = emailAddressIsValid();
      let entitiesValid = entitiesListIsValid();
      return emailValid && entitiesValid;
  }

  return (
    <div className="App">
        <h2>Count the number of times biological entities are mentioned in the C. elegans literature</h2>
        <h3>Powered by <a href="https://textpressocentral.org" target="_blank" rel="noopener noreferrer"><Chip label="TextpressoCentral" color="primary"/></a></h3><br/>
        <TextField
          id="outlined-multiline-static"
          label="Insert entities, one per line"
          multiline
          rows={20}
          defaultValue=""
          variant="outlined"
          value={entities.join('\n')}
          error={entitiesError !== null}
          helperText={entitiesError}
          onChange={(event) => setEntities(event.target.value.split('\n'))} /><br/>
        <TextField id="standard-basic" label="Send results to" value={emailAddress} error={emailError !== null} helperText={emailError} onChange={(event) => setEmailAddress(event.target.value)} /><br/>
        <FormControl>
            <InputLabel id="demo-simple-select-label">Statistics</InputLabel>
            <Select labelId="demo-simple-select-label" value={opType} onChange={(event) => setOpType(event.target.value)}>
                <option value="total_count">Total Count</option>
                <option value="vars_in_paper">Entities in each paper</option>
                <option value="papers_per_var">Papers mentioning each entity</option>
            </Select>
        </FormControl><br/><br/>

        <Button onClick={() => {
            if (inputIsValid()) {
                axios
                    .post(process.env.REACT_APP_API_ENDPOINT, {variations: entities, replyto: emailAddress, type: opType})
                    .then(res => {
                        if (res.status === 200) {
                            setOpenDialog("Request submitted. You will receive the results to the provided email address.");
                        } else {
                            setOpenDialog("Error: Wrong request format.");
                        }
                    })
                    .catch(err => {
                        setOpenDialog(err.message);
                    });
            }
        }}>Calculate</Button>

        <Dialog
            open={openDialog !== null}
            onClose={() => setOpenDialog(null)}
            aria-labelledby="alert-dialog-title"
            aria-describedby="alert-dialog-description"
        >
            <DialogTitle id="alert-dialog-title">{"Success"}</DialogTitle>
            <DialogContent>
                <DialogContentText id="alert-dialog-description">
                    {openDialog}
                </DialogContentText>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => setOpenDialog(null)} color="primary">
                    Close
                </Button>
            </DialogActions>
        </Dialog>
    </div>
  );
}

export default App;
