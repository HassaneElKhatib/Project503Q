import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const key = import.meta.env.VITE_SUPABASE_ANON_KEY;

const isSupabaseConfigured = Boolean(url && key);
const supabase = isSupabaseConfigured ? createClient(url, key) : null;

export default function uploadFile(file){
  const promise = new Promise(
    (resolve, reject) => {
      if(!file){
        reject("No file provided");
        return;
      }

      if (!supabase) {
        reject("File upload is unavailable: configure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.");
        return;
      }

      const timeStamp = new Date().getTime();
      const fileName = timeStamp+"-"+ file.name;

      supabase.storage.from("skyrek-img").upload(fileName, file,{
        cacheControl: "3600",
        upsert: false

      }).then(
        () => {

          const publicUrl = supabase.storage.from("skyrek-img").getPublicUrl(fileName).data.publicUrl;
          resolve(publicUrl);

        }
      ).catch(
        () => {
          reject("Failed to upload file");
        }
      )

    }
  )
  return promise;
}