export default function isAdmin(res) {

  if(res.data.role === "admin"){
    return true;
  }else{
    return false;
  }
}