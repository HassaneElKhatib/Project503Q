import { useState } from "react";
const FALLBACK_IMAGE =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400'><rect width='100%25' height='100%25' fill='%23f3f4f6'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%239ca3af' font-family='Arial' font-size='24'>No image</text></svg>";

export default function ImageSlider({images}){ // const images = props.images;
  const safeImages = (images || []).filter((image) => Boolean(image));
  const[activeImageIndex, setActiveImageIndex] = useState(0);
  const activeImage = safeImages[activeImageIndex] || FALLBACK_IMAGE;

  return(
    <div className="w-[300px] h-[400px] md:w-[400px] md:h-[500px]">
      <img src={activeImage} className="w-full h-[320px] md:h-[400px] object-cover" />
      <div className="w-full h-[50px] md:px-0 mt-[15px] md:mt-0 md:h-[100px] flex flex-row items-center justify-center gap-1">
        {
          safeImages.map(
            (image, index)=> {
              return(
                <img src={image || FALLBACK_IMAGE} key={index} className={"w-[70px] h-[70px] md:w-[90px] md:h-[90px] object-cover cursor-pointer" + (activeImageIndex == index ? " border-[3px]" : "")} 
                onClick={
                  ()=> {
                    setActiveImageIndex(index);
                  }
                }/>
              )
            }
          )
        }
      </div>
    </div>
  )
}