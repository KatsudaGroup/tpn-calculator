from PIL import Image, ImageDraw, ImageFont
import pandas as pd

class WesternBlotPlotUtil:
    def __init__(self, data, plot_sample_indices: list, mw_column_index = 0,
                 band_width: int = 20, band_spacing: int = 10, offset: int = 20, marker_molecular_weights = [],
                 label_font_size = 16, marker_font_size = 12,
                 plot_labels = []):
        self.set_data(data)
        self.set_plot_indices(plot_sample_indices)
        self.set_plot_labels(plot_labels)
        self.set_band_width(band_width, band_spacing)
        self.mw_column_index = mw_column_index
        self.set_marker_molecular_weights(marker_molecular_weights)

        self.set_offset_uniform(offset)
        self.set_font_size(label_font_size= label_font_size, marker_font_size=marker_font_size)

        self.image_size = None
        self.field_rectangle = None

        self.set_molecular_weight_range()  # Default value is None

    def set_offset_uniform(self, offset): 
        self.offset_left = offset
        self.offset_right = offset
        self.offset_top = offset
        self.offset_bottom = offset

    def set_offset(self, 
                   offset_left = None, offset_right = None,
                   offset_top = None, offset_bottom = None):
        if offset_left != None:
            self.offset_left = offset_left
        if offset_right != None:
            self.offset_right = offset_right
        if offset_top != None:
            self.offset_top = offset_top
        if offset_bottom != None:
            self.offset_bottom = offset_bottom

    def set_molecular_weight_range(self, mw_range_min = None, mw_range_max = None):
        # If None is set, draw the to the min or max edge.
        self.mw_range_min = mw_range_min
        self.mw_range_max = mw_range_max

    def calc_image_size(self, sorted_data):
        n_lanes = len(self.plot_indices)
        band_width = self.band_width
        band_spacing = self.band_spacing
        data_length = len(sorted_data)
        
        offset_left = self.offset_left
        offset_right = self.offset_right
        offset_top = self.offset_top
        offset_bottom = self.offset_bottom
        
        field_width = (band_width + band_spacing) * n_lanes + band_spacing
        field_height = data_length

        image_width = field_width + offset_left + offset_right
        image_height= data_length + offset_top + offset_bottom

        image_size = (image_width, image_height)
        field_rectangle = ((offset_left, offset_top), (offset_left + field_width, offset_top + field_height))
        return image_size, field_rectangle


    def set_data(self, data: pd.DataFrame):
        self.data = data.copy()


    def set_plot_indices(self, plot_indices: list[int]):
        # Error check
        for i in plot_indices:
            if not i < len(self.data.columns):
                raise
        self.plot_indices = plot_indices.copy()

    def set_plot_labels(self, plot_labels: list):
        # Error check
        if len(self.plot_indices) < len(plot_labels):
            raise
        self.plot_labels = plot_labels
            

    def set_plot_samples(self, sample_name_list: list[str]):
        # Convert sample names into column index
        self.plot_indices = []
        for sample_name in sample_name_list:
            try:
                index = self.data.columns.index(sample_name)
                self.plot_indices.append(index)
            except:
                raise

    def set_band_width(self, band_width: int, band_spacing: int):
        if band_width < 0 or band_spacing < 0:
            raise
        self.band_width = band_width
        self.band_spacing = band_spacing

    def set_font_size(self, label_font_size = None, marker_font_size = None):
        if label_font_size < 0 or marker_font_size < 0:
            raise
        if label_font_size != None:
            self.label_font_size = label_font_size
        if marker_font_size != None:
            self.marker_font_size = marker_font_size

    def set_marker_molecular_weights(self, marker_mw_list: list[tuple[int|float, str|None]]):
        self.marker_molecular_weights = marker_mw_list


    def calc_normalized_signal(self, signal_raw_value, signal_upper_bound):
        signal_in_range = min(signal_raw_value, signal_upper_bound)
        signal_normalized = signal_in_range / signal_upper_bound
        signal_for_plot =  int(255 * (1 - signal_normalized))
        return signal_for_plot


    def molecular_weight_reorder(self):
        mw_key = self.data.columns[self.mw_column_index]
        if isinstance(self.data, pd.DataFrame) and self.data.empty == False:
            sorted_data = self.data.sort_values(by = mw_key, ascending = False).reset_index(drop = True)
            return sorted_data
        else:
            raise

    def search_max_signal(self, plot_data):
        signal_max = 0
        for i in self.plot_indices:
            signal_max_in_lane = plot_data.iloc[:,i].max()
            signal_max = max(signal_max, signal_max_in_lane)
        return signal_max
    
    def determine_mw_range_index(self, sorted_data):
        # Search the index correspond to specified molecular weight bound
        mw_series_full = sorted_data.iloc[:, self.mw_column_index]
        mw_min_in_data = mw_series_full[len(mw_series_full) - 1]
        mw_max_in_data = mw_series_full[0]
        
        min_row_index = len(mw_series_full)
        if self.mw_range_min != None and mw_min_in_data < self.mw_range_min:
            min_row_index = (mw_series_full - self.mw_range_min).abs().idxmin()
            min_row_index = min(len(mw_series_full), min_row_index)

        max_row_index = 0
        if self.mw_range_max != None and self.mw_range_max < mw_max_in_data:
            max_row_index = (mw_series_full - self.mw_range_max).abs().idxmin()

        return max_row_index, min_row_index


    def draw_bands(self, signal_max = None, draw_rectangle = True, draw_marker_line = False, write_text = False, write_label = False, rotate_label = False):
        def generate_line_start_x_func(bandwidth, bandspacing, offsetx):
            return lambda i: i * (bandwidth + bandspacing) + bandspacing + offsetx
        #----------------------------------------
        # Setup the dataset
        #----------------------------------------
        sorted_data_ = self.molecular_weight_reorder()
        max_row_index, min_row_index = self.determine_mw_range_index(sorted_data_)

        sorted_data = sorted_data_.iloc[max_row_index:min_row_index]
        sorted_data.reset_index(drop = True, inplace = True)
        
        #----------------------------------------
        # Calc the image size and set up the canvas
        #----------------------------------------
        if self.image_size == None or self.field_rectangle == None:
            self.image_size, self.field_rectangle = self.calc_image_size(sorted_data)

        im_ = Image.new('L', self.image_size, color = 255)
        draw_ = ImageDraw.Draw(im_)
        (field_origin_x, field_origin_y) = self.field_rectangle[0]

        band_spacing = self.band_spacing
        band_width = self.band_width
        calc_line_start_x = generate_line_start_x_func(band_width, band_spacing, field_origin_x)
        
        #----------------------------------------
        # Set up the signal max
        #----------------------------------------
        if signal_max == None:
            signal_max = self.search_max_signal(sorted_data)
        else:
            pass

        #----------------------------------------
        # Draw Labels
        #----------------------------------------
        lane_num_offset_y = 8
        baseline_y = field_origin_y - lane_num_offset_y
        if write_label == True:
            lane_font_size = self.label_font_size
            lane_font = ImageFont.load_default(lane_font_size)    # For now, use default font.
            ascent, descent = lane_font.getmetrics()
            for i_lane in range(len(self.plot_indices)):
                label_text = "{}".format(self.plot_labels[i_lane] if self.plot_labels[i_lane] != None else "")
                left, top, right, bottom = lane_font.getbbox(label_text)
                text_width = right - left
                text_height = bottom - top

                line_start_x = calc_line_start_x(i_lane)
                line_end_x = line_start_x + band_width
                text_start_x = (line_start_x + line_end_x) / 2 - text_width / 2

                if rotate_label == False:
                    text_start_y = baseline_y - ascent
                    draw_.text((text_start_x, text_start_y), label_text, 0, font = lane_font)
                else:
                    text_bbox_margin = 10 
                    baseline_y = field_origin_y - lane_num_offset_y // 2
                    w_, h_ = text_width + text_bbox_margin, ascent + descent + text_bbox_margin
                    #text_image = Image.new('L', (w_, h_), color = 255)
                    text_image = Image.new('RGBA', (w_, h_), (0,0,0,0))
                    text_draw = ImageDraw.Draw(text_image)
                    text_draw.text((text_bbox_margin//2, ascent - text_height), label_text, font = lane_font, fill = (0,0,0,255))
                    text_image = text_image.rotate(90, expand = True)
                    text_start_y = baseline_y - w_
                    text_start_x = line_start_x + (band_width  - h_ )// 2
                    im_.paste(text_image, (text_start_x, text_start_y), text_image)


        #----------------------------------------
        # Draw Bands
        #----------------------------------------
        for row_index, record in sorted_data.iterrows():
            for i_lane, i_plot in enumerate(self.plot_indices):
                signal_raw = record.iloc[i_plot]

                line_start_x = calc_line_start_x(i_lane)
                line_end_x   = line_start_x + band_width
                line_y = row_index + field_origin_y
                gray_scale_signal = self.calc_normalized_signal(signal_raw, signal_max)
                draw_.line( ((line_start_x, line_y), (line_end_x, line_y)), fill = gray_scale_signal )

                if row_index == 0:
                    pass

        if draw_rectangle == True:
            draw_.rectangle(self.field_rectangle, outline = 0, width = 2)
        
        #----------------------------------------
        # Draw Marker and Marker-Label
        #----------------------------------------
        if draw_marker_line == True or write_text == True:
            text_right_offset = 1
            marker_line_length = 5 
            marker_start_x = field_origin_x - marker_line_length
            marker_end_x = field_origin_x
            mw_series = sorted_data.iloc[:, self.mw_column_index]
            # Filter
            marker_weights_in_range = []
            if 0 < len(mw_series):
                marker_weights_in_range = [x for x in self.marker_molecular_weights if mw_series[len(mw_series)-1] <= x[0] and x[0] <= mw_series[0] ]
            
            # Load font
            if write_text == True:
                font_size = self.marker_font_size
                font = ImageFont.load_default(font_size)    # For now, use default font.
                mw_font_ascent, mw_font_descent = font.getmetrics()
                mw_font_vcenter_offset = (mw_font_ascent + mw_font_descent) / 2

            for marker_mw in marker_weights_in_range:
                row_index = (mw_series - marker_mw[0]).abs().argmin()
                line_y = row_index + field_origin_y

                if draw_marker_line == True:
                    draw_.line(((marker_start_x, line_y), (marker_end_x, line_y)), 0, width = 3)
                
                if write_text == True:
                    text = "{}".format(marker_mw[1] if marker_mw[1] != None else marker_mw[0])
                    
                    # Texts are aligned at Right edge.
                    left, top, right, bottom = font.getbbox(text)
                    text_width = right - left
                    text_start_x = marker_start_x - text_right_offset - text_width
                    text_height = bottom - top
                    text_y = line_y - mw_font_vcenter_offset
                    draw_.text((marker_start_x - text_right_offset - text_width, int(text_y)), text, 0, font = font)

        self.image = im_
        return True


    def save_png(self, filename):
        self.image.save(filename)


    def get_image_obj(self):
        if self.image != None:
            return self.image
        else:
            raise


if __name__ == '__main__':
    filename = "example/20240424_Abby txt data.xlsx"
    raw_data = pd.read_excel(filename)

    plot_obj = WesternBlotPlotUtil(raw_data, plot_sample_indices = [1,2,3,4,5,6,7,8], mw_column_index = 0, offset = 30, marker_molecular_weights = [230, 180, 116, 66, 40, 12])
    plot_obj.set_molecular_weight_range(100, 300)
    plot_obj.draw_bands(signal_max = 10000)
    plot_obj.save_png('hogehoge.png')
    #plot_obj.get_image_obj()
